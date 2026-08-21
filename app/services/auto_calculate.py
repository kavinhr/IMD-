from sqlalchemy import event
from app import db
from app.models import DailyObservation, Observation, Parameter
from sqlalchemy import func
from datetime import datetime

def update_monthly_observation(mapper, connection, target):
    """
    Event listener triggered after a DailyObservation is inserted/updated/deleted.
    It recalculates the monthly aggregated value and updates the Observation table.
    """
    # Use the session associated with the target
    session = db.session
    
    # We need to know which parameter it is
    param = Parameter.query.get(target.parameter_id)
    if not param:
        return
        
    monthly_param_code = None
    if param.parameter_code == 'TEMP_MAX':
        monthly_param_code = ['TEMP_MAX_HIGH', 'TEMP_MAX_MEAN']
    elif param.parameter_code == 'TEMP_MIN':
        monthly_param_code = ['TEMP_MIN_LOW', 'TEMP_MIN_MEAN']
    elif param.parameter_code == 'RAINFALL':
        monthly_param_code = ['RAINFALL_MAX_24HR', 'RAINFALL_TOTAL', 'RAINY_DAYS']
    elif param.parameter_code == 'DAILY_RH_0830':
        monthly_param_code = ['RH_0830_MEAN', 'RH_0830_HIGH', 'RH_0830_LOW']
    elif param.parameter_code == 'DAILY_RH_1730':
        monthly_param_code = ['RH_1730_MEAN', 'RH_1730_HIGH', 'RH_1730_LOW']
    elif param.parameter_code == 'DAILY_WIND_SPEED':
        monthly_param_code = ['WIND_SPEED_MEAN']
        
    if not monthly_param_code:
        return

    # Calculate aggregations for the month
    if isinstance(monthly_param_code, list):
        codes = monthly_param_code
    else:
        codes = [monthly_param_code]
        
    for code in codes:
        monthly_param = Parameter.query.filter_by(parameter_code=code).first()
        if not monthly_param:
            continue
            
        # Get all daily observations for this station, year, month
        daily_obs = DailyObservation.query.filter_by(
            station_id=target.station_id,
            parameter_id=target.parameter_id,
            obs_year=target.obs_year,
            obs_month=target.obs_month
        ).all()
        
        valid_obs = [o for o in daily_obs if o.obs_value is not None]
        if not valid_obs:
            # Maybe delete the monthly if it exists? Or just leave it as missing.
            continue
            
        extreme_val = None
        extreme_date = None
        
        if code in ['TEMP_MAX_HIGH', 'RH_0830_HIGH', 'RH_1730_HIGH', 'RAINFALL_MAX_24HR']:
            extreme_obj = max(valid_obs, key=lambda x: x.obs_value)
            extreme_val = extreme_obj.obs_value
            extreme_date = extreme_obj.obs_day
        elif code in ['TEMP_MIN_LOW', 'RH_0830_LOW', 'RH_1730_LOW']:
            extreme_obj = min(valid_obs, key=lambda x: x.obs_value)
            extreme_val = extreme_obj.obs_value
            extreme_date = extreme_obj.obs_day
        elif code in ['TEMP_MAX_MEAN', 'TEMP_MIN_MEAN', 'RH_0830_MEAN', 'RH_1730_MEAN', 'WIND_SPEED_MEAN']:
            if valid_obs:
                extreme_val = round(sum(o.obs_value for o in valid_obs) / len(valid_obs), 1)
            else:
                extreme_val = None
            extreme_date = None
        elif code == 'RAINFALL_TOTAL':
            extreme_val = round(sum(o.obs_value for o in valid_obs), 1)
            extreme_date = None
        elif code == 'RAINY_DAYS':
            extreme_val = sum(1 for o in valid_obs if o.obs_value >= 2.5)
            extreme_date = None
            
        # Upsert Observation
        # First check if it's already in the current session
        obs = None
        for obj in session:
            if isinstance(obj, Observation) and \
               obj.station_id == target.station_id and \
               obj.parameter_id == monthly_param.parameter_id and \
               obj.obs_year == target.obs_year and \
               obj.obs_month == target.obs_month:
                obs = obj
                break
                
        if not obs:
            obs = Observation.query.filter_by(
                station_id=target.station_id,
                parameter_id=monthly_param.parameter_id,
                obs_year=target.obs_year,
                obs_month=target.obs_month
            ).first()
        
        if obs:
            obs.obs_value = extreme_val
            obs.date_of_extreme = extreme_date
            obs.updated_at = datetime.utcnow()
        else:
            obs = Observation(
                station_id=target.station_id,
                parameter_id=monthly_param.parameter_id,
                obs_year=target.obs_year,
                obs_month=target.obs_month,
                obs_value=extreme_val,
                date_of_extreme=extreme_date,
                entered_at=datetime.utcnow()
            )
            session.add(obs)
            
def register_listeners():
    event.listen(DailyObservation, 'after_insert', update_monthly_observation)
    event.listen(DailyObservation, 'after_update', update_monthly_observation)
    event.listen(DailyObservation, 'after_delete', update_monthly_observation)
