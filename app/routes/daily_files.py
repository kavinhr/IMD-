from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required
from app.models import Station, DailyObservation, Parameter
from app import db
import pandas as pd
import io

daily_files_bp = Blueprint('daily_files', __name__)

@daily_files_bp.route('/')
@login_required
def index():
    """List all stations for daily file download"""
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    
    station_stats = []
    for s in stations:
        count = DailyObservation.query.filter_by(station_id=s.station_id).count()
        station_stats.append({
            'station': s,
            'record_count': count
        })
        
    return render_template('daily_files/index.html', station_stats=station_stats)

@daily_files_bp.route('/download/<int:station_id>')
@login_required
def download(station_id):
    """Generate and download the Daily Master Excel file for a station"""
    station = Station.query.get_or_404(station_id)
    
    observations = DailyObservation.query.filter_by(station_id=station_id).all()
    
    if not observations:
        flash(f'No daily data available for {station.station_name} yet.', 'warning')
        return redirect(url_for('daily_files.index'))
        
    output = io.BytesIO()
    
    # We want to group by year and month to create sheets, e.g., "JAN_2026", "FEB_2026"
    df_obs = []
    for obs in observations:
        val = obs.obs_value if obs.obs_value is not None else obs.value_text
        df_obs.append({
            'YEAR': obs.obs_year,
            'MONTH': obs.obs_month,
            'DAY': obs.obs_day,
            'PARAM_CODE': obs.parameter.parameter_code,
            'VALUE': val
        })
        
    df = pd.DataFrame(df_obs)
    month_names = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL', 5: 'MAY', 6: 'JUNE', 
                   7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER'}
                   
    # The columns in the Excel file
    columns_mapping = {
        'TEMP_MAX': 'MAX.TEMP',
        'TEMP_MIN': 'MIN.TEMP',
        'RAINFALL': 'RF: 0830 Hrs',
        'DAILY_SUNSHINE': 'SUN SHINE',
        'DAILY_RH_0830': 'RH : 0830',
        'DAILY_RH_1730': 'RH : 1730',
        'DAILY_WIND_SPEED': 'Avg. wind 24 Hrs.(Kmph)'
    }
    
    ordered_columns = ['Date', 'MAX.TEMP', 'MIN.TEMP', 'RF: 0830 Hrs', 'SUN SHINE', 'RH : 0830', 'RH : 1730', 'Avg. wind 24 Hrs.(Kmph)']
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        title_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter'
        })
        
        default_cell = workbook.add_format({'align': 'center', 'border': 1})
        date_cell = workbook.add_format({'align': 'center', 'border': 1, 'bold': True})
        
        # Number formats
        fmt_1_dec = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '0.0'})
        fmt_rf = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '000.0'})
        fmt_sun = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '00.0'})
        fmt_int = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '0'})
        fmt_wind = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '000'})
        
        # Mapping column names to their specific format
        col_formats = {
            'Date': date_cell,
            'MAX.TEMP': fmt_1_dec,
            'MIN.TEMP': fmt_1_dec,
            'RF: 0830 Hrs': fmt_rf,
            'SUN SHINE': fmt_sun,
            'RH : 0830': fmt_int,
            'RH : 1730': fmt_int,
            'Avg. wind 24 Hrs.(Kmph)': fmt_wind
        }
        
        # Group by year and month
        groups = df.groupby(['YEAR', 'MONTH'])
        
        for (year, month), group in groups:
            month_name = month_names.get(month, f"M{month}")
            sheet_name = f"{month_name[:3]}_{year}"
            worksheet = workbook.add_worksheet(sheet_name)
            writer.sheets[sheet_name] = worksheet
            
            # Set column widths
            worksheet.set_column('A:A', 8)
            worksheet.set_column('B:C', 12)
            worksheet.set_column('D:D', 14)
            worksheet.set_column('E:E', 12)
            worksheet.set_column('F:G', 12)
            worksheet.set_column('H:H', 24)
            
            # Form the IMD header
            worksheet.merge_range('A1:H1', f"STATION STATEMENT {month_name} {year} PBO {station.station_name.upper()}", title_format)
            
            # Write column headers
            header_row = 1
            for col_num, col_name in enumerate(ordered_columns):
                worksheet.write(header_row, col_num, col_name, header_format)
            
            # Pivot the group to have DAY as index and PARAM_CODE as columns
            pivot = group.pivot_table(index='DAY', columns='PARAM_CODE', values='VALUE', aggfunc='first')
            
            data_row = header_row + 1
            totals = {col: 0.0 for col in ordered_columns[1:]}
            counts = {col: 0 for col in ordered_columns[1:]}
            
            for day in range(1, 32):
                worksheet.write(data_row, 0, day, date_cell)
                for col_num, col_name in enumerate(ordered_columns[1:], 1):
                    param_code = [k for k, v in columns_mapping.items() if v == col_name]
                    cell_fmt = col_formats[col_name]
                    
                    written = False
                    if param_code:
                        param_code = param_code[0]
                        if param_code in pivot.columns and day in pivot.index:
                            val = pivot.loc[day, param_code]
                            if pd.notnull(val):
                                # If it's numeric, add to total
                                try:
                                    val_float = float(val)
                                    totals[col_name] += val_float
                                    counts[col_name] += 1
                                    worksheet.write_number(data_row, col_num, val_float, cell_fmt)
                                except ValueError:
                                    # Write string (like Trace)
                                    worksheet.write_string(data_row, col_num, str(val), default_cell)
                                written = True
                                
                    if not written:
                        worksheet.write_blank(data_row, col_num, "", default_cell)
                        
                data_row += 1
                
            # Write TOTAL row
            worksheet.write(data_row, 0, "TOTAL", date_cell)
            for col_num, col_name in enumerate(ordered_columns[1:], 1):
                if counts[col_name] > 0:
                    worksheet.write_number(data_row, col_num, totals[col_name], fmt_1_dec) # Totals are usually 1 decimal place
                else:
                    worksheet.write_blank(data_row, col_num, "", default_cell)
            data_row += 1
            
            # Write AVERAGE row
            worksheet.write(data_row, 0, "AVERAGE", date_cell)
            for col_num, col_name in enumerate(ordered_columns[1:], 1):
                # Don't average Rainfall usually, according to the screenshot it's blank
                if col_name == 'RF: 0830 Hrs':
                    worksheet.write_blank(data_row, col_num, "", default_cell)
                    continue
                    
                if counts[col_name] > 0:
                    avg = totals[col_name] / counts[col_name]
                    # Avg is usually 1 decimal place or int
                    if col_name in ['RH : 0830', 'RH : 1730', 'Avg. wind 24 Hrs.(Kmph)']:
                        worksheet.write_number(data_row, col_num, round(avg), fmt_int)
                    else:
                        worksheet.write_number(data_row, col_num, avg, fmt_1_dec)
                else:
                    worksheet.write_blank(data_row, col_num, "", default_cell)

    output.seek(0)
    
    filename = f"{station.station_code}_Daily_Master.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)
