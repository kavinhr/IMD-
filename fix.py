with open('app/models.py', 'r') as f:
    content = f.read()

import re

match = re.search(r'class StationExtremeRecord\(db\.Model\):', content)
if match:
    content = content[:match.start()]

new_code = """class StationExtremeRecord(db.Model):
    \"\"\"Manually edited all-time extreme weather records for a station\"\"\"
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
    date_of_extreme = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    station = db.relationship('Station')
    parameter = db.relationship('Parameter')
    
    def __repr__(self):
        return f'<WordDocExtremeData Station:{self.station_id} Year:{self.obs_year} Month:{self.obs_month} Param:{self.parameter_id}>'
"""

content += new_code
with open('app/models.py', 'w') as f:
    f.write(content)
