"""
Database models for Weather Data Management System
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Role(db.Model):
    """User roles"""
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'security'}
    
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    role_description = db.Column(db.Text)
    permissions = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.role_name}>'
    
    def has_permission(self, permission):
        """Check if role has specific permission"""
        if self.permissions:
            return self.permissions.get(permission, False) or self.permissions.get('all', False)
        return False


class User(UserMixin, db.Model):
    """User accounts"""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'security'}
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('security.roles.role_id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    password_expires_at = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    observations_entered = db.relationship('Observation', foreign_keys='Observation.entered_by', 
                                          backref='entered_by_user', lazy='dynamic')
    observations_updated = db.relationship('Observation', foreign_keys='Observation.updated_by',
                                          backref='updated_by_user', lazy='dynamic')
    daily_observations_entered = db.relationship('DailyObservation', foreign_keys='DailyObservation.entered_by', 
                                          backref='daily_entered_by_user', lazy='dynamic')
    daily_observations_updated = db.relationship('DailyObservation', foreign_keys='DailyObservation.updated_by',
                                          backref='daily_updated_by_user', lazy='dynamic')
    
    def get_id(self):
        """Override for Flask-Login"""
        return str(self.user_id)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return self.role.has_permission(permission)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Station(db.Model):
    """Meteorological stations"""
    __tablename__ = 'stations'
    __table_args__ = {'schema': 'core'}
    
    station_id = db.Column(db.Integer, primary_key=True)
    station_code = db.Column(db.String(20), unique=True, nullable=False)
    station_name = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(50))
    state = db.Column(db.String(50), default='Tamil Nadu')
    latitude = db.Column(db.Numeric(9, 6))
    longitude = db.Column(db.Numeric(9, 6))
    elevation = db.Column(db.Integer)
    station_type = db.Column(db.String(30))
    operational_from = db.Column(db.Integer)
    operational_to = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    station_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    observations = db.relationship('Observation', backref='station', lazy='dynamic')
    daily_observations = db.relationship('DailyObservation', backref='station', lazy='dynamic')
    parameter_stations = db.relationship('ParameterStation', backref='station', lazy='dynamic')
    
    def __repr__(self):
        return f'<Station {self.station_code}: {self.station_name}>'


class Parameter(db.Model):
    """Meteorological parameters"""
    __tablename__ = 'parameters'
    __table_args__ = {'schema': 'core'}
    
    parameter_id = db.Column(db.Integer, primary_key=True)
    parameter_code = db.Column(db.String(50), unique=True, nullable=False)
    parameter_name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(30))
    category = db.Column(db.String(50))
    data_type = db.Column(db.String(20))
    min_value = db.Column(db.Numeric(10, 2))
    max_value = db.Column(db.Numeric(10, 2))
    decimal_places = db.Column(db.SmallInteger, default=1)
    aggregation_type = db.Column(db.String(30))
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    parameter_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    observations = db.relationship('Observation', backref='parameter', lazy='dynamic')
    daily_observations = db.relationship('DailyObservation', backref='parameter', lazy='dynamic')
    parameter_stations = db.relationship('ParameterStation', backref='parameter', lazy='dynamic')
    
    def __repr__(self):
        return f'<Parameter {self.parameter_code}: {self.parameter_name}>'



class ParameterStation(db.Model):
    """Parameter availability at stations"""
    __tablename__ = 'parameter_station'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('core.parameters.parameter_id'), nullable=False)
    data_start_year = db.Column(db.Integer)
    data_end_year = db.Column(db.Integer)
    data_completeness = db.Column(db.Numeric(5, 2))
    total_records = db.Column(db.Integer, default=0)
    last_observation_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('station_id', 'parameter_id', name='uq_station_parameter'),
        {'schema': 'core'}
    )
    
    def __repr__(self):
        return f'<ParameterStation S:{self.station_id} P:{self.parameter_id}>'


class Observation(db.Model):
    """Meteorological observations"""
    __tablename__ = 'observations'
    __table_args__ = {'schema': 'core'}
    
    observation_id = db.Column(db.BigInteger, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('core.parameters.parameter_id'), nullable=False)
    obs_year = db.Column(db.Integer, nullable=False)
    obs_month = db.Column(db.Integer, nullable=False)
    obs_value = db.Column(db.Numeric(12, 4))
    value_text = db.Column(db.String(50))
    data_quality_flag = db.Column(db.String(10))
    is_validated = db.Column(db.Boolean, default=False)
    is_estimated = db.Column(db.Boolean, default=False)
    is_anomaly = db.Column(db.Boolean, default=False)
    remarks = db.Column(db.Text)
    source_file = db.Column(db.String(255))
    entered_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    entered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    updated_at = db.Column(db.DateTime)
    date_of_extreme = db.Column(db.String(50))  # Can hold dates like "01,26", for Extreme Weather Events Report
    
    __table_args__ = (
        db.UniqueConstraint('station_id', 'parameter_id', 'obs_year', 'obs_month', 
                          name='uq_observation'),
        db.CheckConstraint('obs_year >= 1900 AND obs_year <= 2100', name='check_year'),
        db.CheckConstraint('obs_month >= 1 AND obs_month <= 12', name='check_month'),
        db.CheckConstraint('obs_value IS NOT NULL OR value_text IS NOT NULL', 
                          name='check_value_or_text'),
        {'schema': 'core'}
    )
    
    data_quality_issues = db.relationship('DataQualityIssue', backref='observation', lazy='dynamic')
    
    def __repr__(self):
        return f'<Observation S:{self.station_id} P:{self.parameter_id} {self.obs_year}-{self.obs_month:02d}>'


class DailyObservation(db.Model):
    """Daily meteorological observations"""
    __tablename__ = 'daily_observations'
    __table_args__ = {'schema': 'core'}
    
    observation_id = db.Column(db.BigInteger, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('core.parameters.parameter_id'), nullable=False)
    obs_year = db.Column(db.Integer, nullable=False)
    obs_month = db.Column(db.Integer, nullable=False)
    obs_day = db.Column(db.Integer, nullable=False)
    obs_value = db.Column(db.Numeric(12, 4))
    value_text = db.Column(db.String(50))
    data_quality_flag = db.Column(db.String(10))
    is_validated = db.Column(db.Boolean, default=False)
    is_estimated = db.Column(db.Boolean, default=False)
    is_anomaly = db.Column(db.Boolean, default=False)
    remarks = db.Column(db.Text)
    source_file = db.Column(db.String(255))
    entered_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    entered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    updated_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('station_id', 'parameter_id', 'obs_year', 'obs_month', 'obs_day', 
                          name='uq_daily_observation'),
        db.CheckConstraint('obs_year >= 1900 AND obs_year <= 2100', name='check_daily_year'),
        db.CheckConstraint('obs_month >= 1 AND obs_month <= 12', name='check_daily_month'),
        db.CheckConstraint('obs_day >= 1 AND obs_day <= 31', name='check_daily_day'),
        db.CheckConstraint('obs_value IS NOT NULL OR value_text IS NOT NULL', 
                          name='check_daily_value_or_text'),
        {'schema': 'core'}
    )
    
    data_quality_issues = db.relationship('DataQualityIssue', foreign_keys='DataQualityIssue.daily_observation_id', backref='daily_observation', lazy='dynamic')
    
    def __repr__(self):
        return f'<DailyObservation S:{self.station_id} P:{self.parameter_id} {self.obs_year}-{self.obs_month:02d}-{self.obs_day:02d}>'


class DataQualityIssue(db.Model):
    """Data quality issues tracking"""
    __tablename__ = 'data_quality_issues'
    __table_args__ = {'schema': 'quality'}
    
    issue_id = db.Column(db.BigInteger, primary_key=True)
    observation_id = db.Column(db.BigInteger, db.ForeignKey('core.observations.observation_id'))
    daily_observation_id = db.Column(db.BigInteger, db.ForeignKey('core.daily_observations.observation_id'))
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'))
    parameter_id = db.Column(db.Integer, db.ForeignKey('core.parameters.parameter_id'))
    obs_year = db.Column(db.Integer)
    obs_month = db.Column(db.Integer)
    issue_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20))
    issue_description = db.Column(db.Text)
    detected_value = db.Column(db.String(100))
    expected_range = db.Column(db.String(100))
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    detected_by = db.Column(db.String(50), default='SYSTEM')
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    resolution_notes = db.Column(db.Text)
    resolution_action = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<DataQualityIssue {self.issue_type}: {self.issue_description}>'


class AuditLog(db.Model):
    """Audit logs for all actions"""
    __tablename__ = 'audit_logs'
    __table_args__ = {'schema': 'audit'}
    
    audit_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    action_type = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(100))
    record_id = db.Column(db.BigInteger)
    old_value = db.Column(db.JSON)
    new_value = db.Column(db.JSON)
    query_executed = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    execution_time = db.Column(db.Integer)
    status = db.Column(db.String(20))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<AuditLog {self.action_type} by User:{self.user_id}>'


class ExcelFile(db.Model):
    """Excel archive files"""
    __tablename__ = 'excel_files'
    __table_args__ = {'schema': 'archive'}
    
    file_id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'))
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    file_hash = db.Column(db.String(64))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    migrated = db.Column(db.Boolean, default=False)
    migration_date = db.Column(db.DateTime)
    
    station = db.relationship('Station', backref='excel_files')
    uploaded_by_user = db.relationship('User', backref='uploaded_files', foreign_keys=[uploaded_by])
    migration_histories = db.relationship('MigrationHistory', backref='excel_file', lazy='dynamic')
    
    def __repr__(self):
        return f'<ExcelFile {self.file_name}>'

class DailyExcelFile(db.Model):
    """Daily Excel archive files"""
    __tablename__ = 'daily_excel_files'
    __table_args__ = {'schema': 'archive'}
    
    file_id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'))
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    file_hash = db.Column(db.String(64))
    obs_year = db.Column(db.Integer)
    obs_month = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    migrated = db.Column(db.Boolean, default=False)
    migration_date = db.Column(db.DateTime)
    
    station = db.relationship('Station', backref='daily_excel_files')
    uploaded_by_user = db.relationship('User', backref='daily_uploaded_files', foreign_keys=[uploaded_by])
    migration_histories = db.relationship('DailyMigrationHistory', backref='daily_excel_file', lazy='dynamic')
    
    def __repr__(self):
        return f'<DailyExcelFile {self.file_name}>'



class MigrationHistory(db.Model):
    """Migration history tracking"""
    __tablename__ = 'migration_history'
    __table_args__ = {'schema': 'archive'}
    
    migration_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('archive.excel_files.file_id'))
    migration_start = db.Column(db.DateTime, default=datetime.utcnow)
    migration_end = db.Column(db.DateTime)
    records_processed = db.Column(db.Integer, default=0)
    records_success = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_log = db.Column(db.JSON)
    migrated_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    status = db.Column(db.String(20), default='PENDING')
    
    migrated_by_user = db.relationship('User', backref='migrations', foreign_keys=[migrated_by])
    
    def __repr__(self):
        return f'<MigrationHistory {self.migration_id}: {self.status}>'

class DailyMigrationHistory(db.Model):
    """Daily migration history tracking"""
    __tablename__ = 'daily_migration_history'
    __table_args__ = {'schema': 'archive'}
    
    migration_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('archive.daily_excel_files.file_id'))
    migration_start = db.Column(db.DateTime, default=datetime.utcnow)
    migration_end = db.Column(db.DateTime)
    records_processed = db.Column(db.Integer, default=0)
    records_success = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_log = db.Column(db.JSON)
    migrated_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'))
    status = db.Column(db.String(20), default='PENDING')
    
    migrated_by_user = db.relationship('User', backref='daily_migrations', foreign_keys=[migrated_by])
    
    def __repr__(self):
        return f'<DailyMigrationHistory {self.migration_id}: {self.status}>'


class StationExtremeRecord(db.Model):
    """Manually edited all-time extreme weather records for a station"""
    __tablename__ = 'station_extreme_records'
    __table_args__ = (
        db.UniqueConstraint('station_id', 'month', name='uq_station_extreme_month'),
        {'schema': 'core'}
    )
    
    record_id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'), nullable=False)
    month = db.Column(db.Integer, nullable=False) # 1-12
    
    highest_tmax = db.Column(db.Numeric(10, 2))
    highest_tmax_date = db.Column(db.String(10)) # Store as string like "04" to allow flexibility
    highest_tmax_year = db.Column(db.Integer)
    
    lowest_tmin = db.Column(db.Numeric(10, 2))
    lowest_tmin_date = db.Column(db.String(10))
    lowest_tmin_year = db.Column(db.Integer)
    
    highest_daily_rf = db.Column(db.Numeric(10, 2))
    highest_daily_rf_date = db.Column(db.String(10))
    highest_daily_rf_year = db.Column(db.Integer)
    
    highest_monthly_rf = db.Column(db.Numeric(10, 2))
    highest_monthly_rf_year = db.Column(db.Integer)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('security.users.user_id'), nullable=True)
    
    # Relationships
    station = db.relationship('Station', backref=db.backref('extreme_records', lazy=True))
    
    def __repr__(self):
        return f'<StationExtremeRecord Station:{self.station_id} Month:{self.month}>'

class WordDocExtremeData(db.Model):
    __tablename__ = 'word_doc_extreme_data'
    __table_args__ = {'schema': 'core'}
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('core.stations.station_id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('core.parameters.parameter_id'), nullable=False)
    obs_year = db.Column(db.Integer, nullable=False)
    obs_month = db.Column(db.Integer, nullable=False)
    obs_value = db.Column(db.Numeric(10, 2), nullable=False)
    date_of_extreme = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    station = db.relationship('Station')
    parameter = db.relationship('Parameter')
    
    def __repr__(self):
        return f'<WordDocExtremeData Station:{self.station_id} Year:{self.obs_year} Month:{self.obs_month} Param:{self.parameter_id}>'
