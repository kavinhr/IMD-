"""Station Overview routes"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.models import Station, Parameter, Observation, DailyObservation
from app import db
from sqlalchemy import func

station_overview_bp = Blueprint('station_overview', __name__)

@station_overview_bp.route('/')
@login_required
def index():
    """Station Overview interface"""
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    parameters = Parameter.query.filter_by(is_active=True).order_by(Parameter.display_order).all()
    daily_params = Parameter.query.filter(Parameter.parameter_code.in_(['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED'])).all()
    monthly_params = Parameter.query.filter(~Parameter.parameter_code.in_(['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED'])).all()
    parameters = Parameter.query.filter_by(is_active=True).order_by(Parameter.display_order).all()
    
    # Get all distinct years in the database for the year range picker
    years_result = db.session.query(Observation.obs_year).distinct().order_by(Observation.obs_year).all()
    available_years = [y[0] for y in years_result] if years_result else []
    
    return render_template('station_overview/index.html', 
                           stations=stations, 
                           parameters=parameters,
                           daily_params=daily_params,
                           monthly_params=monthly_params,
                           available_years=available_years)

@station_overview_bp.route('/api/records')
@login_required
def get_records():
    """Get highest and lowest records for a station"""
    station_id = request.args.get('station_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    
    data_type = request.args.get('data_type', 'monthly')
    
    ModelClass = Observation if data_type == 'monthly' else DailyObservation
    
    query_highest = db.session.query(ModelClass).filter(
        ModelClass.station_id == station_id,
        ModelClass.obs_value.isnot(None)
    )
    query_lowest = db.session.query(ModelClass).filter(
        ModelClass.station_id == station_id,
        ModelClass.obs_value.isnot(None)
    )
    
    if parameter_id:
        query_highest = query_highest.filter(ModelClass.parameter_id == parameter_id)
        query_lowest = query_lowest.filter(ModelClass.parameter_id == parameter_id)
        
    highest_records = query_highest.distinct(ModelClass.parameter_id).order_by(
        ModelClass.parameter_id,
        ModelClass.obs_value.desc(),
        ModelClass.obs_year.desc(),
        ModelClass.obs_month.desc()
    ).all()
    
    lowest_records = query_lowest.distinct(ModelClass.parameter_id).order_by(
        ModelClass.parameter_id,
        ModelClass.obs_value.asc(),
        ModelClass.obs_year.desc(),
        ModelClass.obs_month.desc()
    ).all()
    
    # Format the response
    records = []
    
    # We want to iterate through all active parameters (or just the selected one)
    if parameter_id:
        params = Parameter.query.filter_by(parameter_id=parameter_id, is_active=True).all()
    else:
        q = Parameter.query.filter_by(is_active=True)
        daily_codes = ['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED']
        if data_type == 'monthly':
            q = q.filter(~Parameter.parameter_code.in_(daily_codes))
        else:
            q = q.filter(Parameter.parameter_code.in_(daily_codes))
        params = q.order_by(Parameter.display_order).all()
        
    high_dict = {obs.parameter_id: obs for obs in highest_records}
    low_dict = {obs.parameter_id: obs for obs in lowest_records}
    
    for p in params:
        h_obs = high_dict.get(p.parameter_id)
        l_obs = low_dict.get(p.parameter_id)
        
        if data_type == 'monthly':
            date_fmt_h = f"{h_obs.obs_month:02d}/{h_obs.obs_year}" if h_obs else "-"
            date_fmt_l = f"{l_obs.obs_month:02d}/{l_obs.obs_year}" if l_obs else "-"
        else:
            date_fmt_h = f"{h_obs.obs_day:02d}/{h_obs.obs_month:02d}/{h_obs.obs_year}" if h_obs else "-"
            date_fmt_l = f"{l_obs.obs_day:02d}/{l_obs.obs_month:02d}/{l_obs.obs_year}" if l_obs else "-"
            
        records.append({
            'parameter_name': p.parameter_name,
            'highest_value': float(h_obs.obs_value) if h_obs else None,
            'highest_date': date_fmt_h,
            'lowest_value': float(l_obs.obs_value) if l_obs else None,
            'lowest_date': date_fmt_l
        })
        
    return jsonify({'records': records})

@station_overview_bp.route('/api/chart-data')
@login_required
def chart_data():
    """Get data for charts"""
    station_id = request.args.get('station_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    year_from = request.args.get('year_from', type=int)
    year_to = request.args.get('year_to', type=int)
    data_type = request.args.get('data_type', 'monthly')
    daily_month = request.args.get('daily_month', type=int)
    daily_year = request.args.get('daily_year', type=int)
    months = request.args.getlist('month', type=int)
    if not months and daily_month:
        months = [daily_month]
    
    ModelClass = Observation if data_type == 'monthly' else DailyObservation
    
    query = ModelClass.query.filter(
        ModelClass.station_id == station_id,
        ModelClass.parameter_id == parameter_id
    )
    
    if data_type == 'monthly':
        if year_from:
            query = query.filter(ModelClass.obs_year >= year_from)
        if year_to:
            query = query.filter(ModelClass.obs_year <= year_to)
        if months:
            query = query.filter(ModelClass.obs_month.in_(months))
        observations = query.order_by(ModelClass.obs_year, ModelClass.obs_month).all()
    else:
        if daily_year:
            query = query.filter(ModelClass.obs_year == daily_year)
        if months:
            query = query.filter(ModelClass.obs_month.in_(months))
        observations = query.order_by(ModelClass.obs_year, ModelClass.obs_month, ModelClass.obs_day).all()
    
    data = {
        'labels': [],
        'values': []
    }
    
    for obs in observations:
        if data_type == 'monthly':
            data['labels'].append(f"{obs.obs_year}-{obs.obs_month:02d}")
        else:
            data['labels'].append(f"{obs.obs_month:02d}-{obs.obs_day:02d}")
        data['values'].append(float(obs.obs_value) if obs.obs_value else None)
    
    return jsonify(data)

@station_overview_bp.route('/api/table-data')
@login_required
def table_data():
    """Get data formatted for an HTML table (Years x Months)"""
    station_id = request.args.get('station_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    data_type = request.args.get('data_type', 'monthly')
    daily_month = request.args.get('daily_month', type=int)
    daily_year = request.args.get('daily_year', type=int)
    
    if not station_id or not parameter_id:
        return jsonify({'error': 'Station and Parameter are required'}), 400
        
    ModelClass = Observation if data_type == 'monthly' else DailyObservation
    
    query = ModelClass.query.filter(
        ModelClass.station_id == station_id,
        ModelClass.parameter_id == parameter_id
    )
    
    if data_type == 'monthly':
        observations = query.order_by(ModelClass.obs_year.desc(), ModelClass.obs_month).all()
        # Group by year
        years_data = {}
        for obs in observations:
            y = obs.obs_year
            m = obs.obs_month
            if y not in years_data:
                years_data[y] = {i: '-' for i in range(1, 13)}
                
            years_data[y][m] = float(obs.obs_value) if obs.obs_value is not None else obs.value_text or '-'
            
        table_rows = []
        for year in sorted(years_data.keys(), reverse=True):
            row = {'period': year}
            for m in range(1, 13):
                row[f'v{m}'] = years_data[year][m]
            table_rows.append(row)
    else:
        if daily_year:
            query = query.filter(ModelClass.obs_year == daily_year)
        if daily_month:
            query = query.filter(ModelClass.obs_month == daily_month)
        
        observations = query.order_by(ModelClass.obs_year.desc(), ModelClass.obs_month.desc(), ModelClass.obs_day).all()
        # Group by year/month
        months_data = {}
        for obs in observations:
            ym = f"{obs.obs_year}-{obs.obs_month:02d}"
            d = obs.obs_day
            if ym not in months_data:
                months_data[ym] = {i: '-' for i in range(1, 32)}
                
            months_data[ym][d] = float(obs.obs_value) if obs.obs_value is not None else obs.value_text or '-'
            
        table_rows = []
        for ym in sorted(months_data.keys(), reverse=True):
            row = {'period': ym}
            for d in range(1, 32):
                row[f'v{d}'] = months_data[ym][d]
            table_rows.append(row)
        
        
    return jsonify({'data': table_rows})

@station_overview_bp.route('/api/daily_grid')
@login_required
def daily_grid():
    """Get grid data for ALL daily parameters (Parameters x Days 1-31)"""
    station_id = request.args.get('station_id', type=int)
    daily_year = request.args.get('daily_year', type=int)
    daily_month = request.args.get('daily_month', type=int)
    
    if not station_id or not daily_year or not daily_month:
        return jsonify({'error': 'Station, Year, and Month are required'}), 400
        
    daily_codes = ['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED']
    params = Parameter.query.filter(Parameter.parameter_code.in_(daily_codes), Parameter.is_active == True).order_by(Parameter.display_order).all()
    
    observations = DailyObservation.query.filter(
        DailyObservation.station_id == station_id,
        DailyObservation.obs_year == daily_year,
        DailyObservation.obs_month == daily_month
    ).all()
    
    # Organize by parameter_id -> day -> value
    obs_dict = {}
    for obs in observations:
        if obs.parameter_id not in obs_dict:
            obs_dict[obs.parameter_id] = {}
        obs_dict[obs.parameter_id][obs.obs_day] = float(obs.obs_value) if obs.obs_value is not None else obs.value_text
        
    table_rows = []
    for param in params:
        row = {'parameter_name': param.parameter_name}
        for d in range(1, 32):
            val = obs_dict.get(param.parameter_id, {}).get(d, '-')
            row[f'v{d}'] = val if val is not None else '-'
        table_rows.append(row)
        
    return jsonify({'data': table_rows})

@station_overview_bp.route('/api/monthly_grid')
@login_required
def monthly_grid():
    """Get grid data for ALL monthly parameters (Parameters x Months Jan-Dec)"""
    station_id = request.args.get('station_id', type=int)
    year = request.args.get('year', type=int)
    
    if not station_id or not year:
        return jsonify({'error': 'Station and Year are required'}), 400
        
    daily_codes = ['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED']
    params = Parameter.query.filter(~Parameter.parameter_code.in_(daily_codes), Parameter.is_active == True).order_by(Parameter.display_order).all()
    
    observations = Observation.query.filter(
        Observation.station_id == station_id,
        Observation.obs_year == year
    ).all()
    
    # Organize by parameter_id -> month -> value
    obs_dict = {}
    for obs in observations:
        if obs.parameter_id not in obs_dict:
            obs_dict[obs.parameter_id] = {}
        obs_dict[obs.parameter_id][obs.obs_month] = float(obs.obs_value) if obs.obs_value is not None else obs.value_text
        
    table_rows = []
    for param in params:
        row = {'parameter_name': param.parameter_name}
        for m in range(1, 13):
            val = obs_dict.get(param.parameter_id, {}).get(m, '-')
            row[f'v{m}'] = val if val is not None else '-'
        table_rows.append(row)
        
    return jsonify({'data': table_rows})
