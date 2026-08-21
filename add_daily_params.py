import sys
from app import create_app, db
from app.models import Parameter, DailyExcelFile, DailyMigrationHistory

def main():
    app = create_app()
    with app.app_context():
        # Create new tables
        DailyExcelFile.__table__.create(db.engine, checkfirst=True)
        DailyMigrationHistory.__table__.create(db.engine, checkfirst=True)
        print("Created new tables for daily files.")

        parameters_data = [
            {
                'parameter_code': 'DAILY_RH_0830',
                'parameter_name': 'Daily Relative Humidity at 0830 hrs',
                'unit': '%',
                'category': 'HUMIDITY',
                'data_type': 'NUMERIC',
                'min_value': 0.0,
                'max_value': 100.0,
                'decimal_places': 0,
                'aggregation_type': 'MEAN',
                'display_order': 18
            },
            {
                'parameter_code': 'DAILY_RH_1730',
                'parameter_name': 'Daily Relative Humidity at 1730 hrs',
                'unit': '%',
                'category': 'HUMIDITY',
                'data_type': 'NUMERIC',
                'min_value': 0.0,
                'max_value': 100.0,
                'decimal_places': 0,
                'aggregation_type': 'MEAN',
                'display_order': 19
            },
            {
                'parameter_code': 'DAILY_WIND_SPEED',
                'parameter_name': 'Daily Average Wind Speed',
                'unit': 'KMPH',
                'category': 'WIND',
                'data_type': 'NUMERIC',
                'min_value': 0.0,
                'max_value': 150.0,
                'decimal_places': 0,
                'aggregation_type': 'MEAN',
                'display_order': 20
            },
            {
                'parameter_code': 'DAILY_SUNSHINE',
                'parameter_name': 'Daily Sunshine Hours',
                'unit': 'HOURS',
                'category': 'OTHER',
                'data_type': 'NUMERIC',
                'min_value': 0.0,
                'max_value': 24.0,
                'decimal_places': 1,
                'aggregation_type': 'TOTAL',
                'display_order': 21
            }
        ]

        for param_data in parameters_data:
            existing_param = Parameter.query.filter_by(parameter_code=param_data['parameter_code']).first()
            if not existing_param:
                param = Parameter(**param_data)
                db.session.add(param)
                print(f"Created parameter {param_data['parameter_name']}")
            else:
                print(f"Parameter {param_data['parameter_code']} already exists")
        
        db.session.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    main()
