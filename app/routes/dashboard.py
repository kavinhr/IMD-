"""
Dashboard routes
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Station, Parameter, Observation, DataQualityIssue

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard"""
    # Check if password change is required
    if current_user.must_change_password:
        return redirect(url_for('auth.change_password'))
    
    # Get statistics
    total_stations = Station.query.filter_by(is_active=True).count()
    total_parameters = Parameter.query.filter_by(is_active=True).count()
    total_observations = Observation.query.count()
    
    # Get recent observations
    recent_observations = Observation.query\
        .join(Station).join(Parameter)\
        .order_by(Observation.entered_at.desc())\
        .limit(10)\
        .all()
    
    # Get All-Time Climate Records
    highest_records = db.session.query(Observation)\
        .filter(Observation.obs_value.isnot(None))\
        .distinct(Observation.parameter_id)\
        .order_by(
            Observation.parameter_id,
            Observation.obs_value.desc(),
            Observation.obs_year.desc(),
            Observation.obs_month.desc()
        ).all()
        
    lowest_records = db.session.query(Observation)\
        .filter(Observation.obs_value.isnot(None))\
        .distinct(Observation.parameter_id)\
        .order_by(
            Observation.parameter_id,
            Observation.obs_value.asc(),
            Observation.obs_year.desc(),
            Observation.obs_month.desc()
        ).all()
        
    all_params = Parameter.query.filter_by(is_active=True).order_by(Parameter.parameter_id).all()
    high_dict = {obs.parameter_id: obs for obs in highest_records}
    low_dict = {obs.parameter_id: obs for obs in lowest_records}
    
    excluded_params = [
        "Monthly Mean RH at 0830 hrs IST",
        "Monthly Highest RH at 0830 hrs IST",
        "Monthly Lowest RH at 0830 hrs IST",
        "Monthly Mean RH at 1730 hrs IST",
        "Monthly Highest RH at 1730 hrs IST",
        "Monthly Lowest RH at 1730 hrs IST",
        "Daily Maximum Temperature",
        "Daily Minimum Temperature",
        "Daily Rainfall"
    ]
    
    climate_records = []
    for p in all_params:
        if p.parameter_name not in excluded_params and p.aggregation_type != 'daily':
            climate_records.append({
                'parameter': p,
                'highest': high_dict.get(p.parameter_id),
                'lowest': low_dict.get(p.parameter_id)
            })
        
    # Get data completeness
    current_year = 2024
    observations_current_year = Observation.query\
        .filter_by(obs_year=current_year).count()
    expected_records = total_stations * total_parameters * 12
    completeness_percentage = (observations_current_year / expected_records * 100) \
        if expected_records > 0 else 0
    
    # Get monthly observation counts for chart
    monthly_counts = db.session.query(
        Observation.obs_month,
        func.count(Observation.observation_id).label('count')
    ).filter(
        Observation.obs_year == current_year
    ).group_by(
        Observation.obs_month
    ).order_by(
        Observation.obs_month
    ).all()
    
    monthly_data = {month: 0 for month in range(1, 13)}
    for month, count in monthly_counts:
        monthly_data[month] = count
    
    return render_template(
        'dashboard/index.html',
        total_stations=total_stations,
        total_parameters=total_parameters,
        total_observations=total_observations,
        recent_observations=recent_observations,
        climate_records=climate_records,
        completeness_percentage=round(completeness_percentage, 1),
        monthly_data=monthly_data,
        current_year=current_year
    )


@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('dashboard/profile.html')
