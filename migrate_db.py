from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Alter Observation table
        db.session.execute(text("ALTER TABLE core.observations ALTER COLUMN date_of_extreme TYPE VARCHAR(50);"))
        print("Updated core.observations")
        
        # Alter WordDocExtremeData table
        db.session.execute(text("ALTER TABLE core.word_doc_extreme_data ALTER COLUMN date_of_extreme TYPE VARCHAR(50);"))
        print("Updated core.word_doc_extreme_data")
        
        db.session.commit()
        print("Migration successful.")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
