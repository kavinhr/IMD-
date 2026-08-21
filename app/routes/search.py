"""
Search routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Station, Parameter, Observation, DailyObservation
from sqlalchemy import and_, or_

search_bp = Blueprint('search', __name__)


@search_bp.route('/')
@login_required
def index():
    """Search interface"""
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    parameters = Parameter.query.filter_by(is_active=True).order_by(Parameter.display_order).all()
    years = list(range(2024, 1979, -1))
    
    return render_template(
        'search/index.html',
        stations=stations,
        parameters=parameters,
        years=years
    )


@search_bp.route('/results', methods=['POST'])
@login_required
def results():
    """Search results"""
    station_ids = request.form.getlist('station_ids')
    parameter_ids = request.form.getlist('parameter_ids')
    year_from = request.form.get('year_from')
    year_to = request.form.get('year_to')
    month_from = request.form.get('month_from')
    month_to = request.form.get('month_to')
    data_type = request.form.get('data_type', 'monthly')
    
    # Build query
    if data_type == 'daily':
        query = DailyObservation.query.join(Station).join(Parameter)
        ModelClass = DailyObservation
    else:
        query = Observation.query.join(Station).join(Parameter)
        ModelClass = Observation
    
    if station_ids:
        query = query.filter(ModelClass.station_id.in_(station_ids))
    
    if parameter_ids:
        query = query.filter(ModelClass.parameter_id.in_(parameter_ids))
    
    if year_from:
        query = query.filter(ModelClass.obs_year >= int(year_from))
    
    if year_to:
        query = query.filter(ModelClass.obs_year <= int(year_to))
    
    if month_from:
        query = query.filter(ModelClass.obs_month >= int(month_from))
    
    if month_to:
        query = query.filter(ModelClass.obs_month <= int(month_to))
    
    # Execute query
    if data_type == 'daily':
        observations = query.order_by(
            ModelClass.obs_year.desc(),
            ModelClass.obs_month.desc(),
            ModelClass.obs_day.desc()
        ).limit(1000).all()
    else:
        observations = query.order_by(
            ModelClass.obs_year.desc(),
            ModelClass.obs_month.desc()
        ).limit(1000).all()
    
    return render_template(
        'search/results.html',
        observations=observations,
        result_count=len(observations),
        data_type=data_type
    )
