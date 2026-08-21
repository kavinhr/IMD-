from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required
from app.models import Station, Observation, Parameter
from app import db
import pandas as pd
import io

station_files_bp = Blueprint('station_files', __name__)

@station_files_bp.route('/')
@login_required
def index():
    """List all stations for file download"""
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    
    # Calculate how many records each station has
    station_stats = []
    for s in stations:
        count = Observation.query.filter_by(station_id=s.station_id).count()
        station_stats.append({
            'station': s,
            'record_count': count
        })
        
    return render_template('station_files/index.html', station_stats=station_stats)

@station_files_bp.route('/download/<int:station_id>')
@login_required
def download(station_id):
    """Generate and download the updated Master Excel file for a station"""
    station = Station.query.get_or_404(station_id)
    
    # Fetch all observations
    observations = Observation.query.filter_by(station_id=station_id).all()
    
    if not observations:
        flash(f'No data available for {station.station_name} yet.', 'warning')
        return redirect(url_for('station_files.index'))
        
    output = io.BytesIO()
    month_names = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN', 
                   7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        # Excel sheet names can be max 31 characters
        sheet_name = f"{station.station_code}_Master"[:31]
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet
        
        # Get unique parameters ordered by display_order
        params = sorted(list(set(obs.parameter for obs in observations)), 
                        key=lambda p: p.display_order or 999)
        
        start_row = 0
        header_format = workbook.add_format({'bold': True})
        
        for i, param in enumerate(params):
            param_obs = [obs for obs in observations if obs.parameter_id == param.parameter_id]
            
            data = []
            for obs in param_obs:
                val = obs.obs_value
                if val is not None:
                    # Round numeric values to 1 decimal place
                    val = round(float(val), 1)
                else:
                    val = obs.value_text
                    
                data.append({
                    'YEAR': obs.obs_year,
                    'Month': obs.obs_month,
                    'Value': val
                })
                
            if not data:
                continue
                
            df = pd.DataFrame(data)
            df_pivot = df.pivot_table(
                index='YEAR', 
                columns='Month', 
                values='Value', 
                aggfunc='first'
            )
            
            # Ensure all 12 months are present in the correct order
            for m in range(1, 13):
                if m not in df_pivot.columns:
                    df_pivot[m] = None
                    
            df_pivot = df_pivot[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
            df_pivot.rename(columns=month_names, inplace=True)
            df_pivot.reset_index(inplace=True)
            
            # Write Parameter Header block
            header_text = f"{i+1}. ELEMENT: {param.parameter_name.upper()}"
            if param.unit:
                header_text += f" ({param.unit})"
            worksheet.write(start_row, 1, header_text, header_format)
            
            # Write the pivot table dataframe below the header
            df_pivot.to_excel(writer, sheet_name=sheet_name, startrow=start_row+2, index=False)
            
            # Move start_row down for the next parameter block (with 4 rows of padding)
            start_row += len(df_pivot) + 6
        
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{station.station_name}_Updated_Master.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
