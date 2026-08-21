"""API routes"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models import Station, Parameter, Observation

api_bp = Blueprint('api', __name__)

@api_bp.route('/stations')
@login_required
def get_stations():
    """Get all stations"""
    stations = Station.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': s.station_id,
        'code': s.station_code,
        'name': s.station_name,
        'district': s.district
    } for s in stations])

@api_bp.route('/parameters')
@login_required
def get_parameters():
    """Get all parameters"""
    parameters = Parameter.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.parameter_id,
        'code': p.parameter_code,
        'name': p.parameter_name,
        'unit': p.unit,
        'category': p.category
    } for p in parameters])

@api_bp.route('/observations')
@login_required
def get_observations():
    """Get observations"""
    station_id = request.args.get('station_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    year = request.args.get('year', type=int)
    
    query = Observation.query
    if station_id:
        query = query.filter_by(station_id=station_id)
    if parameter_id:
        query = query.filter_by(parameter_id=parameter_id)
    if year:
        query = query.filter_by(obs_year=year)
    
    observations = query.limit(1000).all()
    return jsonify([{
        'id': o.observation_id,
        'station_id': o.station_id,
        'parameter_id': o.parameter_id,
        'year': o.obs_year,
        'month': o.obs_month,
        'value': float(o.obs_value) if o.obs_value else None,
        'value_text': o.value_text,
        'quality_flag': o.data_quality_flag
    } for o in observations])
