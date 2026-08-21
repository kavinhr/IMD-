"""
Flask application factory
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import get_config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name=None):
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app.config.from_object(get_config())
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Auto-create PostgreSQL database and initialize tables if needed
    ensure_database_initialized(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create necessary directories
    create_directories(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints + sidebar context processor
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register event listeners
    from app.services.auto_calculate import register_listeners
    register_listeners()
    
    # Register shell context
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Role, Station, Parameter, Observation
        return {
            'db': db,
            'User': User,
            'Role': Role,
            'Station': Station,
            'Parameter': Parameter,
            'Observation': Observation
        }
        
    # Inject current time for templates (e.g. copyright year)
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}
    
    app.logger.info(f'{app.config["APP_NAME"]} started successfully')
    
    return app


def create_directories(app):
    """Create necessary directories if they don't exist"""
    directories = [
        app.config.get('EXCEL_ARCHIVE_FOLDER'),
        app.config.get('DAILY_EXCEL_ARCHIVE_FOLDER'),
        app.config.get('EXPORT_FOLDER'),
        app.config.get('BACKUP_FOLDER'),
        app.config.get('LOG_FOLDER'),
        os.path.join(app.root_path, 'static', 'images'),
        os.path.join(app.root_path, 'static', 'css'),
        os.path.join(app.root_path, 'static', 'js'),
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            app.logger.info(f'Created directory: {directory}')


def configure_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists(app.config['LOG_FOLDER']):
            os.mkdir(app.config['LOG_FOLDER'])
        
        # File handler
        file_handler = RotatingFileHandler(
            os.path.join(app.config['LOG_FOLDER'], 'wdms.log'),
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('WDMS startup')


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.data_entry import data_entry_bp
    from app.routes.search import search_bp
    from app.routes.reports import reports_bp
    from app.routes.station_overview import station_overview_bp
    from app.routes.admin import admin_bp
    from app.routes.excel_archive import excel_archive_bp
    from app.routes.station_files import station_files_bp
    from app.routes.api import api_bp
    from app.routes.extreme_weather import extreme_weather_bp
    from app.routes.import_extreme import import_extreme_bp
    from app.routes.extreme_files import extreme_files_bp
    from app.routes.daily_archive import daily_archive_bp
    from app.routes.daily_files import daily_files_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(data_entry_bp, url_prefix='/data-entry')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(station_overview_bp, url_prefix='/station-overview')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(excel_archive_bp, url_prefix='/excel-archive')
    app.register_blueprint(station_files_bp, url_prefix='/station-files')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(extreme_weather_bp, url_prefix='/extreme-weather')
    app.register_blueprint(import_extreme_bp, url_prefix='/import-extreme')
    app.register_blueprint(extreme_files_bp, url_prefix='/extreme-files')
    app.register_blueprint(daily_archive_bp, url_prefix='/daily-archive')
    app.register_blueprint(daily_files_bp, url_prefix='/daily-files')
    # Context processor: inject stations + parameters into every template for sidebar
    @app.context_processor
    def inject_sidebar_data():
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            from app.models import Station, Parameter
            sidebar_stations = Station.query.filter_by(is_active=True)\
                .order_by(Station.station_name).all()
            sidebar_parameters = Parameter.query.filter_by(is_active=True)\
                .order_by(Parameter.display_order).all()
            return dict(sidebar_stations=sidebar_stations,
                        sidebar_parameters=sidebar_parameters)
        return dict(sidebar_stations=[], sidebar_parameters=[])


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """Register custom Jinja2 filters"""
    
    @app.template_filter('format_date')
    def format_date(value, format='%Y-%m-%d'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('format_number')
    def format_number(value, decimals=1):
        if value is None:
            return ''
        # Force exactly 1 decimal place globally, ignoring any requested precision
        return f'{float(value):.1f}'
    
    @app.template_filter('month_name')
    def month_name(month_num):
        if month_num is None:
            return ''
        try:
            month_num = int(month_num)
        except (ValueError, TypeError):
            return ''
            
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        if 1 <= month_num <= 12:
            return months[month_num - 1]
        return ''


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))


def ensure_database_initialized(app):
    """Automatically check and create PostgreSQL database and tables if missing"""
    try:
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('postgresql://'):
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            base_uri, target_db = db_uri.rsplit('/', 1)
            if '?' in target_db:
                target_db = target_db.split('?')[0]
                
            postgres_db_uri = f"{base_uri}/postgres"
            
            conn = psycopg2.connect(postgres_db_uri)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone()
            if not exists:
                print(f"PostgreSQL database '{target_db}' not found. Creating automatically...")
                cur.execute(f'CREATE DATABASE "{target_db}"')
                print(f"  ✓ Database '{target_db}' created successfully!")
            cur.close()
            conn.close()
            
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            schema_name = "security" if db_uri.startswith('postgresql://') else None
            
            if db_uri.startswith('postgresql://'):
                schemas = ['core', 'security', 'quality', 'archive', 'audit']
                for schema in schemas:
                    db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                db.session.commit()
                
            if not inspector.has_table("users", schema=schema_name) and not inspector.has_table("users"):
                print("Database tables not found. Automatically initializing tables and default admin user...")
                db.create_all()
                import init_db
                init_db.insert_default_roles()
                init_db.insert_default_admin()
                init_db.insert_sample_stations()
                init_db.insert_sample_parameters()
                print("  ✓ Database initialized with default admin user (admin / admin123)!")
    except Exception as e:
        print(f"Notice: Automated database check: {e}")

