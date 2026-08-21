"""
Data entry routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Station, Parameter, Observation, DailyObservation, AuditLog
from sqlalchemy.exc import IntegrityError

data_entry_bp = Blueprint('data_entry', __name__)


@data_entry_bp.route('/')
@login_required
def index():
    """Data entry form"""
    # Check permission
    if not current_user.has_permission('write'):
        flash('You do not have permission to enter data.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    parameters = Parameter.query.filter_by(is_active=True).filter(
        Parameter.parameter_code.in_(['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED'])
    ).order_by(Parameter.display_order).all()
    
    years = list(range(datetime.now().year, 1979, -1))
    months = [
        {'num': 1, 'name': 'January'},
        {'num': 2, 'name': 'February'},
        {'num': 3, 'name': 'March'},
        {'num': 4, 'name': 'April'},
        {'num': 5, 'name': 'May'},
        {'num': 6, 'name': 'June'},
        {'num': 7, 'name': 'July'},
        {'num': 8, 'name': 'August'},
        {'num': 9, 'name': 'September'},
        {'num': 10, 'name': 'October'},
        {'num': 11, 'name': 'November'},
        {'num': 12, 'name': 'December'}
    ]
    
    return render_template(
        'data_entry/form.html',
        stations=stations,
        parameters=parameters,
        years=years,
        months=months
    )


@data_entry_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """Submit observation data"""
    # Check permission
    if not current_user.has_permission('write'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        station_id = int(request.form.get('station_id'))
        parameter_id = int(request.form.get('parameter_id'))
        obs_year = int(request.form.get('obs_year'))
        obs_month = int(request.form.get('obs_month'))
        obs_day = request.form.get('obs_day')
        
        value_input = request.form.get('obs_value', '').strip()
        remarks = request.form.get('remarks', '').strip()
        
        # Validate inputs
        if not all([station_id, parameter_id, obs_year, obs_month]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('data_entry.index'))
        
        if obs_month < 1 or obs_month > 12:
            flash('Invalid month value.', 'danger')
            return redirect(url_for('data_entry.index'))
            
        if obs_day:
            try:
                obs_day = int(obs_day)
                if obs_day < 1 or obs_day > 31:
                    flash('Invalid day value.', 'danger')
                    return redirect(url_for('data_entry.index'))
            except ValueError:
                flash('Invalid day value.', 'danger')
                return redirect(url_for('data_entry.index'))
        else:
            obs_day = None
        
        # Get parameter for validation
        parameter = Parameter.query.get(parameter_id)
        if not parameter:
            flash('Parameter not found.', 'danger')
            return redirect(url_for('data_entry.index'))
        
        # Parse value
        obs_value = None
        value_text = None
        data_quality_flag = 'GOOD'
        
        if value_input:
            # Check for special values
            if value_input.upper() in ['TR', 'TRACE']:
                value_text = 'TR'
                obs_value = 0
                data_quality_flag = 'TRACE'
            elif value_input == '***' or value_input.upper() == 'MISSING':
                value_text = '***'
                data_quality_flag = 'MISSING'
            else:
                try:
                    obs_value = round(float(value_input), 1)
                    
                    # Validate range
                    if parameter.min_value is not None and obs_value < float(parameter.min_value):
                        flash(f'Value below minimum ({parameter.min_value} {parameter.unit}).', 'warning')
                        data_quality_flag = 'SUSPECT'
                    
                    if parameter.max_value is not None and obs_value > float(parameter.max_value):
                        flash(f'Value above maximum ({parameter.max_value} {parameter.unit}).', 'warning')
                        data_quality_flag = 'SUSPECT'
                    
                except ValueError:
                    flash('Invalid numeric value.', 'danger')
                    return redirect(url_for('data_entry.index'))

        
        # Check for existing observation
        ModelClass = DailyObservation if obs_day else Observation
        filter_args = {
            'station_id': station_id,
            'parameter_id': parameter_id,
            'obs_year': obs_year,
            'obs_month': obs_month
        }
        if obs_day:
            filter_args['obs_day'] = obs_day
            
        existing_obs = ModelClass.query.filter_by(**filter_args).first()
        
        if existing_obs:
            # Update existing observation
            old_value = {
                'obs_value': str(existing_obs.obs_value),
                'value_text': existing_obs.value_text
            }
            
            existing_obs.obs_value = obs_value
            existing_obs.value_text = value_text
            existing_obs.data_quality_flag = data_quality_flag
            existing_obs.remarks = remarks if remarks else existing_obs.remarks
            existing_obs.updated_by = current_user.user_id
            existing_obs.updated_at = datetime.utcnow()
            
            action = 'UPDATE'
            message = 'Observation updated successfully!'
            
        else:
            # Create new observation
            create_args = {
                'station_id': station_id,
                'parameter_id': parameter_id,
                'obs_year': obs_year,
                'obs_month': obs_month,
                'obs_value': obs_value,
                'value_text': value_text,
                'data_quality_flag': data_quality_flag,
                'remarks': remarks,
                'entered_by': current_user.user_id,
                'entered_at': datetime.utcnow()
            }
            if obs_day:
                create_args['obs_day'] = obs_day
                
            observation = ModelClass(**create_args)
            db.session.add(observation)
            
            old_value = None
            action = 'INSERT'
            message = 'Observation saved successfully!'
        
        db.session.commit()
        
        # Log action
        audit = AuditLog(
            user_id=current_user.user_id,
            action_type=action,
            table_name='daily_observations' if obs_day else 'observations',
            old_value=old_value,
            new_value={
                'station_id': station_id,
                'parameter_id': parameter_id,
                'obs_year': obs_year,
                'obs_month': obs_month,
                'obs_value': str(obs_value) if obs_value else None,
                'value_text': value_text
            },
            status='SUCCESS'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(message, 'success')
        return redirect(url_for('data_entry.index'))
        
    except IntegrityError as e:
        db.session.rollback()
        flash('Database error: Record may already exist.', 'danger')
        return redirect(url_for('data_entry.index'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving data: {str(e)}', 'danger')
        return redirect(url_for('data_entry.index'))


@data_entry_bp.route('/bulk')
@login_required
def bulk_entry():
    """Bulk data entry form"""
    # Check permission
    if not current_user.has_permission('write'):
        flash('You do not have permission to enter data.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    stations = Station.query.filter_by(is_active=True).order_by(Station.station_name).all()
    parameters = Parameter.query.filter_by(is_active=True).filter(
        ~Parameter.parameter_code.in_(['TEMP_MAX', 'TEMP_MIN', 'RAINFALL', 'DAILY_SUNSHINE', 'DAILY_RH_0830', 'DAILY_RH_1730', 'DAILY_WIND_SPEED'])
    ).order_by(Parameter.display_order).all()
    years = list(range(datetime.now().year, 1979, -1))
    
    return render_template(
        'data_entry/bulk_form.html',
        stations=stations,
        parameters=parameters,
        years=years
    )

@data_entry_bp.route('/api/bulk_data')
@login_required
def get_bulk_data():
    """Fetch existing data for bulk entry form"""
    station_id = request.args.get('station_id')
    obs_year = request.args.get('obs_year')
    
    if not all([station_id, obs_year]):
        return jsonify({'success': False, 'message': 'Missing parameters'})
        
    try:
        observations = Observation.query.filter_by(
            station_id=int(station_id),
            obs_year=int(obs_year)
        ).all()
        
        data = {}
        for obs in observations:
            if obs.parameter_id not in data:
                data[obs.parameter_id] = {}
            if obs.obs_value is not None:
                val = round(float(obs.obs_value), 1)
            else:
                val = obs.value_text
            data[obs.parameter_id][obs.obs_month] = val
            
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@data_entry_bp.route('/api/daily_bulk_data')
@login_required
def get_daily_bulk_data():
    """Fetch existing daily data for the grid form"""
    station_id = request.args.get('station_id')
    obs_year = request.args.get('obs_year')
    obs_month = request.args.get('obs_month')
    
    if not all([station_id, obs_year, obs_month]):
        return jsonify({'success': False, 'message': 'Missing parameters'})
        
    try:
        observations = DailyObservation.query.filter_by(
            station_id=int(station_id),
            obs_year=int(obs_year),
            obs_month=int(obs_month)
        ).all()
        
        data = {}
        for obs in observations:
            if obs.parameter_id not in data:
                data[obs.parameter_id] = {}
            if obs.obs_value is not None:
                val = round(float(obs.obs_value), 1)
            else:
                val = obs.value_text
            data[obs.parameter_id][obs.obs_day] = val
            
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@data_entry_bp.route('/bulk_submit', methods=['POST'])
@login_required
def bulk_submit():
    """Handle bulk submission of 12 months"""
    if not current_user.has_permission('write'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
    try:
        station_id = request.form.get('station_id')
        obs_year = request.form.get('obs_year')
        
        if not all([station_id, obs_year]):
            return jsonify({'success': False, 'message': 'Station and Year are required.'})
            
        station_id = int(station_id)
        obs_year = int(obs_year)
        
        parameters = Parameter.query.filter_by(is_active=True).all()
        
        success_count = 0
        
        for parameter in parameters:
            parameter_id = parameter.parameter_id
            for i in range(1, 13):
                val_input = request.form.get(f'month_{i}_{parameter_id}', '').strip()
                
                existing = Observation.query.filter_by(
                    station_id=station_id, parameter_id=parameter_id, obs_year=obs_year, obs_month=i
                ).first()
                
                if not val_input:
                    if existing:
                        db.session.delete(existing)
                        success_count += 1
                    continue
                    
                obs_value = None
                value_text = None
                data_quality_flag = 'GOOD'
                
                if val_input.upper() in ['TR', 'TRACE']:
                    value_text = 'TR'
                    obs_value = 0
                    data_quality_flag = 'TRACE'
                elif val_input == '***' or val_input.upper() == 'MISSING':
                    value_text = '***'
                    data_quality_flag = 'MISSING'
                else:
                    try:
                        obs_value = round(float(val_input), 1)
                        if parameter.min_value is not None and obs_value < float(parameter.min_value):
                            data_quality_flag = 'SUSPECT'
                        if parameter.max_value is not None and obs_value > float(parameter.max_value):
                            data_quality_flag = 'SUSPECT'
                    except ValueError:
                        continue # Skip invalid numeric formats
                        
                # existing query moved to top of loop
                if existing:
                    existing.obs_value = obs_value
                    existing.value_text = value_text
                    existing.data_quality_flag = data_quality_flag
                    existing.updated_at = datetime.utcnow()
                    existing.updated_by = current_user.user_id
                else:
                    obs = Observation(
                        station_id=station_id,
                        parameter_id=parameter_id,
                        obs_year=obs_year,
                        obs_month=i,
                        obs_value=obs_value,
                        value_text=value_text,
                        data_quality_flag=data_quality_flag,
                        entered_at=datetime.utcnow(),
                        entered_by=current_user.user_id
                    )
                    db.session.add(obs)
                success_count += 1
            
        db.session.commit()
        return jsonify({'success': True, 'message': f'Successfully saved {success_count} observations.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@data_entry_bp.route('/daily_bulk_submit', methods=['POST'])
@login_required
def daily_bulk_submit():
    """Handle bulk submission of 31 days"""
    if not current_user.has_permission('write'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
    try:
        station_id = request.form.get('station_id')
        obs_year = request.form.get('obs_year')
        obs_month = request.form.get('obs_month')
        
        if not all([station_id, obs_year, obs_month]):
            return jsonify({'success': False, 'message': 'Station, Year, and Month are required.'})
            
        station_id = int(station_id)
        obs_year = int(obs_year)
        obs_month = int(obs_month)
        
        parameters = Parameter.query.filter_by(is_active=True).all()
        success_count = 0
        
        for parameter in parameters:
            parameter_id = parameter.parameter_id
            for i in range(1, 32):
                val_input = request.form.get(f'day_{i}_{parameter_id}', '').strip()
                if not val_input:
                    continue
                    
                obs_value = None
                value_text = None
                data_quality_flag = 'GOOD'
                
                if val_input.upper() in ['TR', 'TRACE']:
                    value_text = 'TR'
                    obs_value = 0
                    data_quality_flag = 'TRACE'
                elif val_input == '***' or val_input.upper() == 'MISSING':
                    value_text = '***'
                    data_quality_flag = 'MISSING'
                else:
                    try:
                        obs_value = round(float(val_input), 1)
                        if parameter.min_value is not None and obs_value < float(parameter.min_value):
                            data_quality_flag = 'SUSPECT'
                        if parameter.max_value is not None and obs_value > float(parameter.max_value):
                            data_quality_flag = 'SUSPECT'
                    except ValueError:
                        continue # Skip invalid numeric formats
                        
                existing = DailyObservation.query.filter_by(
                    station_id=station_id, parameter_id=parameter_id, obs_year=obs_year, obs_month=obs_month, obs_day=i
                ).first()
                
                if existing:
                    existing.obs_value = obs_value
                    existing.value_text = value_text
                    existing.data_quality_flag = data_quality_flag
                    existing.updated_at = datetime.utcnow()
                    existing.updated_by = current_user.user_id
                else:
                    obs = DailyObservation(
                        station_id=station_id,
                        parameter_id=parameter_id,
                        obs_year=obs_year,
                        obs_month=obs_month,
                        obs_day=i,
                        obs_value=obs_value,
                        value_text=value_text,
                        data_quality_flag=data_quality_flag,
                        entered_at=datetime.utcnow(),
                        entered_by=current_user.user_id
                    )
                    db.session.add(obs)
                success_count += 1
            
        db.session.commit()
        return jsonify({'success': True, 'message': f'Successfully saved {success_count} daily observations.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
