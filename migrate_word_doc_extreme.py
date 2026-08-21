import sys
import os
from app import create_app, db

app = create_app()

with app.app_context():
    # Import the model to make sure it's registered with SQLAlchemy
    from app.models import WordDocExtremeData
    
    # Create the table
    print("Creating word_doc_extreme_data table...")
    WordDocExtremeData.__table__.create(db.engine)
    print("Table created successfully!")
