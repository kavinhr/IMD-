"""
Configuration settings for Weather Data Management System
"""
import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_NAME = 'Climate Data Management, RMC Chennai'
    ORGANIZATION = 'Indian Meteorological Department - Chennai'
    
    # Database
    # PostgreSQL (production):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:adminimd123@localhost:5432/rmc_chennai'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_EXPIRY_DAYS = 90
    
    # File Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
    BASE_DIR = BASE_DIR
    EXCEL_ARCHIVE_FOLDER = os.path.join(BASE_DIR, 'excel_archive')
    DAILY_EXCEL_ARCHIVE_FOLDER = os.path.join(BASE_DIR, 'daily_archive')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    
    # Logging
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 10
    
    # Pagination
    RECORDS_PER_PAGE = 50
    MAX_SEARCH_RESULTS = 10000
    
    # Data Quality
    OUTLIER_DETECTION_METHOD = 'IQR'  # 'IQR' or 'ZSCORE'
    OUTLIER_THRESHOLD = 3.0
    
    # Reports
    REPORT_LOGO_PATH = os.path.join(BASE_DIR, 'app', 'static', 'images', 'imd_logo.png')
    REPORT_FOOTER_TEXT = '© Indian Meteorological Department, Chennai'
    
    # Backup
    BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2:00 AM
    BACKUP_RETENTION_DAYS = 30
    
    # Timezone
    TIMEZONE = 'Asia/Kolkata'
    
    # Development
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://wdms_user:wdms_password@localhost:5432/wdms_test_db'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
