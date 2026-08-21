"""
Migration script for Extreme Weather Events Report Module
Adds daily parameters, updates Observation table, and creates StationExtremeRecord table.
"""
import sys
from app import create_app, db
from app.models import Parameter, StationExtremeRecord, Observation

def migrate():
    app = create_app()
    with app.app_context():
        # 1. Create StationExtremeRecord table
        try:
            print("Creating StationExtremeRecord table...")
            StationExtremeRecord.__table__.create(db.engine, checkfirst=True)
            print("  - Created core.station_extreme_records table")
        except Exception as e:
            print(f"  - Error creating table: {e}")

        # 2. Add date_of_extreme to Observation table
        try:
            print("Adding date_of_extreme to Observation table...")
            db.session.execute(db.text('ALTER TABLE core.observations ADD COLUMN IF NOT EXISTS date_of_extreme INTEGER'))
            db.session.commit()
            print("  - Added date_of_extreme column")
        except Exception as e:
            print(f"  - Error adding column (might already exist): {e}")
            db.session.rollback()

        # 3. Add daily parameters
        print("Inserting new daily parameters...")
        daily_parameters = [
            {
                'parameter_code': 'TEMP_MAX',
                'parameter_name': 'Daily Maximum Temperature',
                'unit': 'DEG C',
                'category': 'TEMPERATURE',
                'data_type': 'NUMERIC',
                'min_value': -20.0,
                'max_value': 50.0,
                'decimal_places': 1,
                'aggregation_type': 'MAX',
                'display_order': 15
            },
            {
                'parameter_code': 'TEMP_MIN',
                'parameter_name': 'Daily Minimum Temperature',
                'unit': 'DEG C',
                'category': 'TEMPERATURE',
                'data_type': 'NUMERIC',
                'min_value': -20.0,
                'max_value': 40.0,
                'decimal_places': 1,
                'aggregation_type': 'MIN',
                'display_order': 16
            },
            {
                'parameter_code': 'RAINFALL',
                'parameter_name': 'Daily Rainfall',
                'unit': 'MM',
                'category': 'RAINFALL',
                'data_type': 'NUMERIC',
                'min_value': 0.0,
                'max_value': 1000.0,
                'decimal_places': 1,
                'aggregation_type': 'TOTAL',
                'display_order': 17
            }
        ]

        for param_data in daily_parameters:
            existing_param = Parameter.query.filter_by(parameter_code=param_data['parameter_code']).first()
            if not existing_param:
                param = Parameter(**param_data)
                db.session.add(param)
                print(f"  - Parameter '{param_data['parameter_name']}' created")
            else:
                print(f"  - Parameter '{param_data['parameter_code']}' already exists")
        
        try:
            db.session.commit()
            print("  - Committed parameter insertions")
        except Exception as e:
            print(f"  - Error committing parameters: {e}")
            db.session.rollback()

        print("Migration completed.")

if __name__ == '__main__':
    migrate()
