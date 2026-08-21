"""
Database initialization script
Creates all tables and inserts default data
"""
import sys
from app import create_app, db
from app.models import Role, User, Station, Parameter
from datetime import datetime


def create_schemas():
    """Create database schemas"""
    print("Creating database schemas...")
    schemas = ['core', 'security', 'quality', 'archive', 'audit']
    
    for schema in schemas:
        try:
            db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
            print(f"  ✓ Schema '{schema}' created")
        except Exception as e:
            print(f"  ✗ Error creating schema '{schema}': {e}")
    
    db.session.commit()
    print()


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        db.create_all()
        print("  ✓ All tables created successfully")
    except Exception as e:
        print(f"  ✗ Error creating tables: {e}")
        sys.exit(1)
    print()


def insert_default_roles():
    """Insert default user roles"""
    print("Inserting default roles...")
    
    roles_data = [
        {
            'role_name': 'ADMIN',
            'role_description': 'System Administrator with full access',
            'permissions': {'all': True}
        },
        {
            'role_name': 'MET_OFFICER',
            'role_description': 'Meteorological Officer',
            'permissions': {'read': True, 'write': True, 'approve': True, 'report': True}
        },
        {
            'role_name': 'DATA_ENTRY',
            'role_description': 'Data Entry Operator',
            'permissions': {'read': True, 'write': True}
        },
        {
            'role_name': 'READ_ONLY',
            'role_description': 'Read-Only User',
            'permissions': {'read': True}
        }
    ]
    
    for role_data in roles_data:
        existing_role = Role.query.filter_by(role_name=role_data['role_name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"  ✓ Role '{role_data['role_name']}' created")
        else:
            print(f"  - Role '{role_data['role_name']}' already exists")
    
    db.session.commit()
    print()


def insert_default_admin():
    """Create default admin user"""
    print("Creating default admin user...")
    
    admin_role = Role.query.filter_by(role_name='ADMIN').first()
    if not admin_role:
        print("  ✗ Admin role not found!")
        return
    
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        print("  - Admin user already exists")
        return
    
    admin = User(
        username='admin',
        email='admin@imd.gov.in',
        role_id=admin_role.role_id,
        full_name='System Administrator',
        department='IT Department',
        is_active=True,
        must_change_password=True
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    print("  ✓ Default admin user created")
    print("     Username: admin")
    print("     Password: admin123")
    print("     ⚠️  Please change password after first login!")
    print()



def insert_sample_stations():
    """Insert sample station data"""
    print("Inserting sample stations...")
    
    stations_data = [
        {
            'station_code': 'ARP',
            'station_name': 'Adirampattinam',
            'district': 'Thanjavur',
            'state': 'Tamil Nadu',
            'station_type': 'OBSERVATORY',
            'operational_from': 1989,
            'is_active': True
        },
        {
            'station_code': 'CMB',
            'station_name': 'Coimbatore Airport',
            'district': 'Coimbatore',
            'state': 'Tamil Nadu',
            'station_type': 'AIRPORT',
            'operational_from': 1980,
            'is_active': True
        },
        {
            'station_code': 'CHN',
            'station_name': 'Chennai (Nungambakkam)',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'latitude': 13.0827,
            'longitude': 80.2707,
            'elevation': 6,
            'station_type': 'OBSERVATORY',
            'operational_from': 1796,
            'is_active': True
        }
    ]
    
    for station_data in stations_data:
        existing_station = Station.query.filter_by(station_code=station_data['station_code']).first()
        if not existing_station:
            station = Station(**station_data)
            db.session.add(station)
            print(f"  ✓ Station '{station_data['station_name']}' ({station_data['station_code']}) created")
        else:
            print(f"  - Station '{station_data['station_code']}' already exists")
    
    db.session.commit()
    print()


def insert_sample_parameters():
    """Insert sample parameter data"""
    print("Inserting sample parameters...")
    
    parameters_data = [
        {
            'parameter_code': 'TEMP_MAX_MEAN',
            'parameter_name': 'Monthly Mean Maximum Temperature',
            'unit': 'DEG C',
            'category': 'TEMPERATURE',
            'data_type': 'NUMERIC',
            'min_value': -20.0,
            'max_value': 50.0,
            'decimal_places': 1,
            'aggregation_type': 'MEAN',
            'display_order': 1
        },
        {
            'parameter_code': 'TEMP_MAX_HIGH',
            'parameter_name': 'Monthly Highest Maximum Temperature',
            'unit': 'DEG C',
            'category': 'TEMPERATURE',
            'data_type': 'NUMERIC',
            'min_value': -20.0,
            'max_value': 50.0,
            'decimal_places': 1,
            'aggregation_type': 'MAX',
            'display_order': 2
        },
        {
            'parameter_code': 'TEMP_MIN_MEAN',
            'parameter_name': 'Monthly Mean Minimum Temperature',
            'unit': 'DEG C',
            'category': 'TEMPERATURE',
            'data_type': 'NUMERIC',
            'min_value': -20.0,
            'max_value': 40.0,
            'decimal_places': 1,
            'aggregation_type': 'MEAN',
            'display_order': 3
        },
        {
            'parameter_code': 'TEMP_MIN_LOW',
            'parameter_name': 'Monthly Lowest Minimum Temperature',
            'unit': 'DEG C',
            'category': 'TEMPERATURE',
            'data_type': 'NUMERIC',
            'min_value': -20.0,
            'max_value': 40.0,
            'decimal_places': 1,
            'aggregation_type': 'MIN',
            'display_order': 4
        },
        {
            'parameter_code': 'RH_0830_MEAN',
            'parameter_name': 'Monthly Mean RH at 0830 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MEAN',
            'display_order': 5
        },
        {
            'parameter_code': 'RH_0830_HIGH',
            'parameter_name': 'Monthly Highest RH at 0830 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MAX',
            'display_order': 6
        },
        {
            'parameter_code': 'RH_0830_LOW',
            'parameter_name': 'Monthly Lowest RH at 0830 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MIN',
            'display_order': 7
        },
        {
            'parameter_code': 'RH_1730_MEAN',
            'parameter_name': 'Monthly Mean RH at 1730 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MEAN',
            'display_order': 8
        },
        {
            'parameter_code': 'RH_1730_HIGH',
            'parameter_name': 'Monthly Highest RH at 1730 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MAX',
            'display_order': 9
        },
        {
            'parameter_code': 'RH_1730_LOW',
            'parameter_name': 'Monthly Lowest RH at 1730 hrs IST',
            'unit': '%',
            'category': 'HUMIDITY',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 100.0,
            'decimal_places': 0,
            'aggregation_type': 'MIN',
            'display_order': 10
        },
        {
            'parameter_code': 'RAINFALL_TOTAL',
            'parameter_name': 'Monthly Total Rainfall',
            'unit': 'MM',
            'category': 'RAINFALL',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 2000.0,
            'decimal_places': 1,
            'aggregation_type': 'TOTAL',
            'display_order': 11
        },
        {
            'parameter_code': 'RAINFALL_MAX_24HR',
            'parameter_name': 'Monthly Heaviest Rainfall in 24 Hours',
            'unit': 'MM',
            'category': 'RAINFALL',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 1000.0,
            'decimal_places': 1,
            'aggregation_type': 'MAX',
            'display_order': 12
        },
        {
            'parameter_code': 'RAINY_DAYS',
            'parameter_name': 'Number of Rainy Days (2.5mm and above)',
            'unit': 'DAYS',
            'category': 'RAINFALL',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 31.0,
            'decimal_places': 0,
            'aggregation_type': 'TOTAL',
            'display_order': 13
        },
        {
            'parameter_code': 'WIND_SPEED_MEAN',
            'parameter_name': 'Monthly Mean Windspeed',
            'unit': 'KMPH',
            'category': 'WIND',
            'data_type': 'NUMERIC',
            'min_value': 0.0,
            'max_value': 150.0,
            'decimal_places': 0,
            'aggregation_type': 'MEAN',
            'display_order': 14
        }
    ]
    
    for param_data in parameters_data:
        existing_param = Parameter.query.filter_by(parameter_code=param_data['parameter_code']).first()
        if not existing_param:
            param = Parameter(**param_data)
            db.session.add(param)
            print(f"  ✓ Parameter '{param_data['parameter_name']}' created")
        else:
            print(f"  - Parameter '{param_data['parameter_code']}' already exists")
    
    db.session.commit()
    print()


def main():
    """Main initialization function"""
    print("=" * 70)
    print("Weather Data Management System - Database Initialization")
    print("=" * 70)
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create schemas
            create_schemas()
            
            # Create tables
            create_tables()
            
            # Insert default data
            insert_default_roles()
            insert_default_admin()
            insert_sample_stations()
            insert_sample_parameters()
            
            print("=" * 70)
            print("✓ Database initialization completed successfully!")
            print("=" * 70)
            print()
            print("Next steps:")
            print("  1. Start the application: python run.py")
            print("  2. Open browser: http://localhost:5000")
            print("  3. Login with admin/admin123")
            print("  4. Change admin password immediately")
            print()
            
        except Exception as e:
            print()
            print("=" * 70)
            print("✗ Database initialization failed!")
            print("=" * 70)
            print(f"Error: {e}")
            print()
            sys.exit(1)


if __name__ == '__main__':
    main()
