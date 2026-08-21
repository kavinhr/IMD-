import pandas as pd
import numpy as np
from app.models import Observation, Parameter
from app import db
from datetime import datetime
import os

class ExcelImporter:
    def __init__(self, file_path, station_id, user_id):
        self.file_path = file_path
        self.station_id = station_id
        self.user_id = user_id
        # Define the exact 14 parameters listed by the user
        self.parameter_codes = [
            'TEMP_MAX_MEAN',
            'TEMP_MAX_HIGH',
            'TEMP_MIN_MEAN',
            'TEMP_MIN_LOW',
            'RH_0830_MEAN',
            'RH_0830_HIGH',
            'RH_0830_LOW',
            'RH_1730_MEAN',
            'RH_1730_HIGH',
            'RH_1730_LOW',
            'RAINFALL_TOTAL',
            'RAINFALL_MAX_24HR',
            'RAINY_DAYS',
            'WIND_SPEED_MEAN'
        ]

    def process(self):
        try:
            excel_data = pd.read_excel(self.file_path, sheet_name=None)
        except Exception as e:
            return False, f"Failed to read Excel file: {str(e)}"
            
        sheet_names = list(excel_data.keys())
        
        if len(sheet_names) < 14:
            # We will still try to process what's there
            pass
            
        success_count = 0
        
        # Pre-fetch parameters to map codes to IDs
        parameters = Parameter.query.all()
        param_map = {p.parameter_code: p.parameter_id for p in parameters}

        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        try:
            # Extract all tables from all sheets
            all_tables = []
            for sheet_name, df in excel_data.items():
                header_indices = []
                for idx, row in df.iterrows():
                    if any(str(val).strip().upper() == 'JAN' for val in row.values if pd.notnull(val)):
                        header_indices.append(idx)
                
                for j in range(len(header_indices)):
                    start_idx = header_indices[j]
                    end_idx = header_indices[j+1] if j+1 < len(header_indices) else len(df)
                    table_df = df.iloc[start_idx:end_idx].copy()
                    
                    if len(table_df) > 0:
                        # Set columns to header row
                        table_df.columns = table_df.iloc[0]
                        table_df = table_df.iloc[1:].reset_index(drop=True)
                        all_tables.append(table_df)

            for i, table_df in enumerate(all_tables):
                if i >= len(self.parameter_codes):
                    break
                    
                code = self.parameter_codes[i]
                param_id = param_map.get(code)
                if not param_id:
                    continue
                    
                df = table_df
                    
                # Find 'YEAR' column
                year_col = None
                for col in df.columns:
                    if str(col).strip().upper() in ['YEAR', 'YEARS', 'YR']:
                        year_col = col
                        break
                
                if not year_col and len(df.columns) > 0:
                    # Assume first column is year
                    year_col = df.columns[0]
                    
                if not year_col:
                    continue

                # Batch the inserts for performance
                observations_to_add = []
                
                for _, row in df.iterrows():
                    year_val = row.get(year_col)
                    if pd.isna(year_val):
                        continue
                    try:
                        year = int(float(str(year_val).strip()))
                    except ValueError:
                        continue # Not a valid year row
                        
                    for month_idx, month_name in enumerate(months, start=1):
                        # Try to find the exact column name or match ignoring case/spaces
                        col_found = None
                        for col in df.columns:
                            if str(col).strip().upper().startswith(month_name):
                                col_found = col
                                break
                        
                        if not col_found:
                            continue
                            
                        raw_val = row.get(col_found)
                        if pd.isna(raw_val) or str(raw_val).strip() == '' or str(raw_val).strip() == '***':
                            continue
                            
                        val_text = None
                        val_num = None
                        
                        raw_str = str(raw_val).strip()
                        if raw_str.upper() == 'TR':
                            val_num = 0.0
                        else:
                            try:
                                val_num = float(raw_str)
                            except ValueError:
                                val_text = raw_str
                                
                        obs = {
                            'station_id': self.station_id,
                            'parameter_id': param_id,
                            'obs_year': year,
                            'obs_month': month_idx,
                            'obs_value': val_num,
                            'value_text': val_text,
                            'entered_by': self.user_id,
                            'entered_at': datetime.utcnow()
                        }
                        observations_to_add.append(obs)
                
                # Using bulk insert/update approach (upsert)
                if observations_to_add:
                    # Deduplicate observations_to_add keeping the last occurrence
                    unique_obs = {}
                    for obs in observations_to_add:
                        unique_obs[(obs['obs_year'], obs['obs_month'])] = obs
                    observations_to_add = list(unique_obs.values())
                    
                    # Get existing
                    years = list(set(o['obs_year'] for o in observations_to_add))
                    existing_obs = Observation.query.filter(
                        Observation.station_id == self.station_id,
                        Observation.parameter_id == param_id,
                        Observation.obs_year.in_(years)
                    ).all()
                    
                    existing_map = {(o.obs_year, o.obs_month): o for o in existing_obs}
                    
                    for obs_data in observations_to_add:
                        key = (obs_data['obs_year'], obs_data['obs_month'])
                        if key in existing_map:
                            existing = existing_map[key]
                            existing.obs_value = obs_data['obs_value']
                            existing.value_text = obs_data['value_text']
                            existing.updated_at = datetime.utcnow()
                            existing.updated_by = self.user_id
                        else:
                            new_obs = Observation(**obs_data)
                            db.session.add(new_obs)
                        success_count += 1
                        
            db.session.commit()
            return True, f"Successfully imported {success_count} monthly observations."
        except Exception as e:
            db.session.rollback()
            return False, f"Error during import: {str(e)}"
