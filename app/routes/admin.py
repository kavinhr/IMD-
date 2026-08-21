"""Admin routes"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Role, Station, Parameter, DataQualityIssue

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def check_admin():
    """Ensure user is admin"""
    if not current_user.has_permission('all'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))

@admin_bp.route('/')
def index():
    """Admin dashboard"""
    users_count = User.query.count()
    stations_count = Station.query.count()
    parameters_count = Parameter.query.count()
    quality_issues_count = DataQualityIssue.query.filter_by(is_resolved=False).count()
    
    return render_template('admin/index.html',
                         users_count=users_count,
                         stations_count=stations_count,
                         parameters_count=parameters_count,
                         quality_issues_count=quality_issues_count)

@admin_bp.route('/users')
def users():
    """Manage users"""
    all_users = User.query.order_by(User.username).all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=all_users, roles=roles)

@admin_bp.route('/users/add', methods=['POST'])
def add_user():
    """Add a new user"""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    department = request.form.get('department')
    phone = request.form.get('phone')
    is_active = request.form.get('is_active') == 'on'
    
    if not username or not email or not password or not full_name or not role_id:
        flash('Username, Email, Password, Full Name and Role are required.', 'danger')
        return redirect(url_for('admin.users'))
        
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash('Username or Email already exists.', 'danger')
        return redirect(url_for('admin.users'))
        
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role_id=role_id,
        department=department,
        phone=phone,
        is_active=is_active
    )
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {username} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding user.', 'danger')
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    department = request.form.get('department')
    phone = request.form.get('phone')
    is_active = request.form.get('is_active') == 'on'
    
    if not username or not email or not full_name or not role_id:
        flash('Username, Email, Full Name and Role are required.', 'danger')
        return redirect(url_for('admin.users'))
        
    existing_user = User.query.filter(
        ((User.username == username) | (User.email == email)) & (User.user_id != user_id)
    ).first()
    if existing_user:
        flash('Username or Email already exists.', 'danger')
        return redirect(url_for('admin.users'))
        
    user.username = username
    user.email = email
    user.full_name = full_name
    user.role_id = role_id
    user.department = department
    user.phone = phone
    user.is_active = is_active
    
    if password:
        user.set_password(password)
        
    try:
        db.session.commit()
        flash(f'User {username} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating user.', 'danger')
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    if user.user_id == current_user.user_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
        
    username = user.username
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot delete user {username} due to associated records. Disable the user instead.', 'danger')
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/stations', methods=['GET', 'POST'])
def stations():
    """Manage stations"""
    if request.method == 'POST':
        station_name = request.form.get('station_name')
        station_code = request.form.get('station_code')
        district = request.form.get('district')
        station_type = request.form.get('station_type', 'SURFACE')
        is_active = request.form.get('is_active') == 'on'
        
        if not station_name or not station_code:
            flash('Station Name and Code are required.', 'danger')
        else:
            existing = Station.query.filter_by(station_code=station_code).first()
            if existing:
                flash('A station with this code already exists.', 'danger')
            else:
                new_station = Station(
                    station_name=station_name,
                    station_code=station_code,
                    district=district,
                    station_type=station_type,
                    is_active=is_active
                )
                db.session.add(new_station)
                db.session.commit()
                flash(f'Station {station_name} added successfully!', 'success')
        return redirect(url_for('admin.stations'))
        
    all_stations = Station.query.order_by(Station.station_name).all()
    return render_template('admin/stations.html', stations=all_stations)

@admin_bp.route('/stations/edit/<int:station_id>', methods=['POST'])
def edit_station(station_id):
    """Edit station"""
    station = Station.query.get_or_404(station_id)
    
    station_name = request.form.get('station_name')
    station_code = request.form.get('station_code')
    district = request.form.get('district')
    station_type = request.form.get('station_type')
    is_active = request.form.get('is_active') == 'on'
    
    if not station_name or not station_code:
        flash('Station Name and Code are required.', 'danger')
    else:
        existing = Station.query.filter(Station.station_code == station_code, Station.station_id != station_id).first()
        if existing:
            flash('A station with this code already exists.', 'danger')
        else:
            station.station_name = station_name
            station.station_code = station_code
            station.district = district
            if station_type:
                station.station_type = station_type
            station.is_active = is_active
            
            try:
                db.session.commit()
                flash(f'Station {station_name} updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the station.', 'danger')
            
    return redirect(url_for('admin.stations'))

@admin_bp.route('/stations/delete/<int:station_id>', methods=['POST'])
def delete_station(station_id):
    """Delete station"""
    station = Station.query.get_or_404(station_id)
    station_name = station.station_name
    
    try:
        db.session.delete(station)
        db.session.commit()
        flash(f'Station {station_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot delete station {station_name} because it has associated data.', 'danger')
        
    return redirect(url_for('admin.stations'))

@admin_bp.route('/parameters')
def parameters():
    """Manage parameters"""
    all_parameters = Parameter.query.order_by(Parameter.display_order).all()
    return render_template('admin/parameters.html', parameters=all_parameters)

@admin_bp.route('/quality')
def quality():
    """Data quality dashboard"""
    issues = DataQualityIssue.query.filter_by(is_resolved=False)\
        .order_by(DataQualityIssue.detected_at.desc()).limit(100).all()
    return render_template('admin/quality.html', issues=issues)
from app.models import StationExtremeRecord

@admin_bp.route('/extreme_records')
def extreme_records():
    """Manage Extreme Records"""
    records = StationExtremeRecord.query.join(Station).order_by(Station.station_name, StationExtremeRecord.month).all()
    stations = Station.query.order_by(Station.station_name).all()
    return render_template('admin/extreme_records.html', records=records, stations=stations)

@admin_bp.route('/extreme_records/add', methods=['POST'])
def add_extreme_record():
    """Add an Extreme Record"""
    station_id = request.form.get('station_id')
    month = request.form.get('month')
    
    if not station_id or not month:
        flash('Station and Month are required.', 'danger')
        return redirect(url_for('admin.extreme_records'))
        
    existing = StationExtremeRecord.query.filter_by(station_id=station_id, month=month).first()
    if existing:
        flash('An extreme record for this station and month already exists.', 'danger')
        return redirect(url_for('admin.extreme_records'))
        
    def parse_num(val): return float(val) if val else None
    def parse_int(val): return int(val) if val else None
    
    record = StationExtremeRecord(
        station_id=station_id,
        month=month,
        highest_tmax=parse_num(request.form.get('highest_tmax')),
        highest_tmax_date=request.form.get('highest_tmax_date') or None,
        highest_tmax_year=parse_int(request.form.get('highest_tmax_year')),
        lowest_tmin=parse_num(request.form.get('lowest_tmin')),
        lowest_tmin_date=request.form.get('lowest_tmin_date') or None,
        lowest_tmin_year=parse_int(request.form.get('lowest_tmin_year')),
        highest_daily_rf=parse_num(request.form.get('highest_daily_rf')),
        highest_daily_rf_date=request.form.get('highest_daily_rf_date') or None,
        highest_daily_rf_year=parse_int(request.form.get('highest_daily_rf_year')),
        highest_monthly_rf=parse_num(request.form.get('highest_monthly_rf')),
        highest_monthly_rf_year=parse_int(request.form.get('highest_monthly_rf_year')),
        updated_by=current_user.user_id
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Extreme record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding extreme record.', 'danger')
        
    return redirect(url_for('admin.extreme_records'))

@admin_bp.route('/extreme_records/edit/<int:record_id>', methods=['POST'])
def edit_extreme_record(record_id):
    """Edit an Extreme Record"""
    record = StationExtremeRecord.query.get_or_404(record_id)
    
    def parse_num(val): return float(val) if val else None
    def parse_int(val): return int(val) if val else None
    
    record.highest_tmax = parse_num(request.form.get('highest_tmax'))
    record.highest_tmax_date = request.form.get('highest_tmax_date') or None
    record.highest_tmax_year = parse_int(request.form.get('highest_tmax_year'))
    record.lowest_tmin = parse_num(request.form.get('lowest_tmin'))
    record.lowest_tmin_date = request.form.get('lowest_tmin_date') or None
    record.lowest_tmin_year = parse_int(request.form.get('lowest_tmin_year'))
    record.highest_daily_rf = parse_num(request.form.get('highest_daily_rf'))
    record.highest_daily_rf_date = request.form.get('highest_daily_rf_date') or None
    record.highest_daily_rf_year = parse_int(request.form.get('highest_daily_rf_year'))
    record.highest_monthly_rf = parse_num(request.form.get('highest_monthly_rf'))
    record.highest_monthly_rf_year = parse_int(request.form.get('highest_monthly_rf_year'))
    record.updated_by = current_user.user_id
    
    try:
        db.session.commit()
        flash('Extreme record updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating extreme record.', 'danger')
        
    return redirect(url_for('admin.extreme_records'))

@admin_bp.route('/extreme_records/delete/<int:record_id>', methods=['POST'])
def delete_extreme_record(record_id):
    """Delete an Extreme Record"""
    record = StationExtremeRecord.query.get_or_404(record_id)
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Extreme record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Cannot delete extreme record.', 'danger')
        
    return redirect(url_for('admin.extreme_records'))
