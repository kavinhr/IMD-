import pandas as pd
import numpy as np
from app.models import DailyObservation, Parameter, Station
from app import db
from datetime import datetime
import re

MONTHS = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']

class DailyExcelImporter:
    def __init__(self, file_path, station_id, user_id, obs_month, obs_year):
        self.file_path = file_path
        self.station_id = station_id
        self.user_id = user_id
        self.obs_month = obs_month
        self.obs_year = obs_year
        
        # Mapping column hints to parameter codes
        self.param_mapping = {
            'MAX': 'TEMP_MAX',
            'MIN': 'TEMP_MIN',
            'RF': 'RAINFALL',
            'RAIN': 'RAINFALL',
            'SUN': 'DAILY_SUNSHINE',
            '0830': 'DAILY_RH_0830', 
            '1730': 'DAILY_RH_1730',
            'WIND': 'DAILY_WIND_SPEED'
        }

    def process(self):
        try:
            # Read all sheets, but usually we just process the first one for daily
            excel_data = pd.read_excel(self.file_path, sheet_name=0, header=None)
        except Exception as e:
            return False, f"Failed to read Excel file: {str(e)}", None, None
            
        success_count = 0
        df = excel_data
        
        # Pre-fetch parameters to map codes to IDs
        parameters = Parameter.query.all()
        param_map = {p.parameter_code: p.parameter_id for p in parameters}
        
        # Use the provided year and month
        obs_year = self.obs_year
        obs_month = self.obs_month

        # Find the header row (contains 'Date')
        header_idx = -1
        for i in range(min(15, len(df))):
            row_vals = [str(x).strip().upper() for x in df.iloc[i].values if pd.notnull(x)]
            if 'DATE' in row_vals or '1' in row_vals:
                if 'DATE' in row_vals:
                    header_idx = i
                elif header_idx == -1:
                    header_idx = max(0, i-1) # Fallback to previous row if Date is not there but 1 is
                break
                
        if header_idx == -1:
            return False, "Could not find the 'Date' header row.", None, None
            
        # Extract column names, looking up to 2 rows for merged headers
        cols = []
        for col_idx in range(len(df.columns)):
            col_name = str(df.iloc[header_idx, col_idx]) if pd.notnull(df.iloc[header_idx, col_idx]) else ""
            if header_idx + 1 < len(df) and (pd.isnull(df.iloc[header_idx, col_idx]) or col_name.strip() == ""):
                 col_name = str(df.iloc[header_idx+1, col_idx]) if pd.notnull(df.iloc[header_idx+1, col_idx]) else ""
            elif header_idx + 1 < len(df) and pd.notnull(df.iloc[header_idx+1, col_idx]):
                 col_name += " " + str(df.iloc[header_idx+1, col_idx])
            cols.append(col_name.upper())

        # Find parameter indices
        param_indices = {}
        for idx, col in enumerate(cols):
            if 'MAX' in col: param_indices['TEMP_MAX'] = idx
            elif 'MIN' in col: param_indices['TEMP_MIN'] = idx
            elif 'RF' in col or 'RAIN' in col: param_indices['RAINFALL'] = idx
            elif 'SUN' in col: param_indices['DAILY_SUNSHINE'] = idx
            elif '0830' in col and 'RH' in col: param_indices['DAILY_RH_0830'] = idx
            elif '1730' in col and 'RH' in col: param_indices['DAILY_RH_1730'] = idx
            elif 'WIND' in col: param_indices['DAILY_WIND_SPEED'] = idx
            elif 'DATE' in col: param_indices['DATE'] = idx
            
        if 'DATE' not in param_indices:
            # Assume first column is date
            param_indices['DATE'] = 0

        observations_to_add = []
        
        # Start reading data after header
        start_row = header_idx + 1
        if start_row < len(df) and str(df.iloc[start_row, param_indices['DATE']]).strip().upper() == 'DATE':
            start_row += 1

        for i in range(start_row, len(df)):
            row = df.iloc[i]
            date_val = row.iloc[param_indices['DATE']]
            
            if pd.isnull(date_val):
                continue
                
            try:
                day = int(float(str(date_val).strip()))
            except ValueError:
                # Skip Total/Mean/Average rows
                continue
                
            if day < 1 or day > 31:
                continue

            for param_code, col_idx in param_indices.items():
                if param_code == 'DATE': continue
                
                param_id = param_map.get(param_code)
                if not param_id: continue
                
                raw_val = row.iloc[col_idx]
                if pd.isnull(raw_val) or str(raw_val).strip() == '' or str(raw_val).strip() == '***':
                    continue
                    
                val_text = None
                val_num = None
                
                raw_str = str(raw_val).strip()
                if raw_str.upper() in ['TR', 'TRACE']:
                    val_num = 0.0
                    val_text = 'TRACE'
                else:
                    try:
                        val_num = float(raw_str)
                    except ValueError:
                        val_text = raw_str
                        
                obs = {
                    'station_id': self.station_id,
                    'parameter_id': param_id,
                    'obs_year': obs_year,
                    'obs_month': obs_month,
                    'obs_day': day,
                    'obs_value': val_num,
                    'value_text': val_text,
                    'entered_by': self.user_id,
                    'entered_at': datetime.utcnow()
                }
                observations_to_add.append(obs)
                
        # Batch insert/update
        if observations_to_add:
            unique_obs = {}
            for obs in observations_to_add:
                unique_obs[(obs['obs_day'], obs['parameter_id'])] = obs
            observations_to_add = list(unique_obs.values())
            
            existing_obs = DailyObservation.query.filter(
                DailyObservation.station_id == self.station_id,
                DailyObservation.obs_year == obs_year,
                DailyObservation.obs_month == obs_month
            ).all()
            
            existing_map = {(o.obs_day, o.parameter_id): o for o in existing_obs}
            
            for obs_data in observations_to_add:
                key = (obs_data['obs_day'], obs_data['parameter_id'])
                if key in existing_map:
                    existing = existing_map[key]
                    existing.obs_value = obs_data['obs_value']
                    existing.value_text = obs_data['value_text']
                    existing.updated_at = datetime.utcnow()
                    existing.updated_by = self.user_id
                else:
                    new_obs = DailyObservation(**obs_data)
                    db.session.add(new_obs)
                success_count += 1
                
        db.session.commit()
        return True, f"Successfully imported {success_count} daily observations for {MONTHS[obs_month-1]} {obs_year}.", obs_year, obs_month

