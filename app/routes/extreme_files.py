from flask import Blueprint, render_template
from flask_login import login_required
from app.models import WordDocExtremeData
from app import db

from app.routes.extreme_weather import get_month_name

extreme_files_bp = Blueprint('extreme_files', __name__)

@extreme_files_bp.route('/')
@login_required
def index():
    """List all months for extreme file download"""
    month_stats = []
    
    for month in range(1, 13):
        # Count all extreme records for this month across all stations
        count = WordDocExtremeData.query.filter_by(obs_month=month).count()
        month_stats.append({
            'month': month,
            'month_name': get_month_name(month),
            'record_count': count
        })
        
    return render_template('extreme_files/index.html', month_stats=month_stats)
