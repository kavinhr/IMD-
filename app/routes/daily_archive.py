"""Daily Excel archive routes"""
from flask import Blueprint, render_template, send_file, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import DailyExcelFile, Station, DailyMigrationHistory
from app import db
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config
from app.services.daily_etl import DailyExcelImporter

daily_archive_bp = Blueprint('daily_archive', __name__)

@daily_archive_bp.route('/')
@login_required
def index():
    """Daily Excel archive browser"""
    files = DailyExcelFile.query.order_by(DailyExcelFile.upload_date.desc()).all()
    stations = Station.query.all()
    return render_template('daily_archive/index.html', files=files, stations=stations)

@daily_archive_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """Download Daily Excel file"""
    file = DailyExcelFile.query.get_or_404(file_id)
    return send_file(file.file_path, as_attachment=True, download_name=file.file_name)

@daily_archive_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})
        
        file = request.files['file']
        station_id = request.form.get('station_id', type=int)
        obs_month = request.form.get('obs_month', type=int)
        obs_year = request.form.get('obs_year', type=int)
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
            
        if not station_id or not obs_month or not obs_year:
            return jsonify({'success': False, 'message': 'Station ID, Month, and Year are required'})
            
        if file:
            filename = secure_filename(file.filename)
            upload_dir = current_app.config.get('DAILY_EXCEL_ARCHIVE_FOLDER', os.path.join(current_app.config['BASE_DIR'], 'daily_archive'))
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            excel_file = DailyExcelFile(
                station_id=station_id,
                file_name=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                uploaded_by=current_user.user_id
            )
            db.session.add(excel_file)
            db.session.commit()
            
            importer = DailyExcelImporter(file_path, station_id, current_user.user_id, obs_month, obs_year)
            success, message, ret_year, ret_month = importer.process()
            
            history = DailyMigrationHistory(
                file_id=excel_file.file_id,
                migration_start=datetime.utcnow(),
                migration_end=datetime.utcnow(),
                migrated_by=current_user.user_id
            )
            
            if success:
                excel_file.migrated = True
                excel_file.migration_date = datetime.utcnow()
                excel_file.obs_year = ret_year
                excel_file.obs_month = ret_month
                history.status = 'SUCCESS'
                db.session.add(history)
                db.session.commit()
                return jsonify({'success': True, 'message': message})
            else:
                history.status = 'FAILED'
                history.error_log = {'error': message}
                db.session.add(history)
                db.session.commit()
                return jsonify({'success': False, 'message': message})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500

@daily_archive_bp.route('/delete_station', methods=['POST'])
@login_required
def delete_station():
    """Delete all uploaded Daily Excel files AND imported observation data for a selected station"""
    from app.models import DailyObservation, DataQualityIssue

    station_id = request.form.get('station_id', type=int)
    if not station_id:
        flash("Station is required.", "danger")
        return redirect(url_for('daily_archive.index'))

    station = Station.query.get_or_404(station_id)

    try:
        # 1. Delete Excel archive file records + physical files
        files = DailyExcelFile.query.filter_by(station_id=station_id).all()
        deleted_files = 0
        for f in files:
            try:
                if os.path.exists(f.file_path):
                    os.remove(f.file_path)
            except Exception:
                pass
            DailyMigrationHistory.query.filter_by(file_id=f.file_id).delete(synchronize_session=False)
            db.session.delete(f)
            deleted_files += 1

        # 2. Delete all daily observations for the station
        deleted_daily = DailyObservation.query.filter_by(station_id=station_id).delete(synchronize_session=False)

        db.session.commit()

        flash(
            f"Successfully purged daily data for {station.station_name}: "
            f"{deleted_files} file record(s), and {deleted_daily} daily observation(s) removed.",
            "success"
        )

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        flash(f"Error deleting data for {station.station_name}: {str(e)}", "danger")

    return redirect(url_for('daily_archive.index'))
