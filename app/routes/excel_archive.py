"""Excel archive routes"""
from flask import Blueprint, render_template, send_file, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import ExcelFile, Station, MigrationHistory
from app import db
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config
from app.services.etl import ExcelImporter

excel_archive_bp = Blueprint('excel_archive', __name__)

@excel_archive_bp.route('/')
@login_required
def index():
    """Excel archive browser"""
    files = ExcelFile.query.order_by(ExcelFile.upload_date.desc()).all()
    stations = Station.query.all()
    return render_template('excel_archive/index.html', files=files, stations=stations)

@excel_archive_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """Download Excel file"""
    file = ExcelFile.query.get_or_404(file_id)
    return send_file(file.file_path, as_attachment=True, download_name=file.file_name)

@excel_archive_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})
        
        file = request.files['file']
        station_id = request.form.get('station_id', type=int)
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
            
        if not station_id:
            return jsonify({'success': False, 'message': 'Station ID is required'})
            
        if file:
            filename = secure_filename(file.filename)
            upload_dir = current_app.config['EXCEL_ARCHIVE_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            excel_file = ExcelFile(
                station_id=station_id,
                file_name=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                uploaded_by=current_user.user_id
            )
            db.session.add(excel_file)
            db.session.commit()
            
            importer = ExcelImporter(file_path, station_id, current_user.user_id)
            success, message = importer.process()
            
            history = MigrationHistory(
                file_id=excel_file.file_id,
                migration_start=datetime.utcnow(),
                migration_end=datetime.utcnow(),
                migrated_by=current_user.user_id
            )
            
            if success:
                excel_file.migrated = True
                excel_file.migration_date = datetime.utcnow()
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

@excel_archive_bp.route('/delete_station', methods=['POST'])
@login_required
def delete_station():
    """Delete all uploaded Excel files AND imported observation data for a selected station"""
    from app.models import Observation, DailyObservation, DataQualityIssue

    station_id = request.form.get('station_id', type=int)
    if not station_id:
        flash("Station is required.", "danger")
        return redirect(url_for('excel_archive.index'))

    station = Station.query.get_or_404(station_id)

    try:
        # 1. Delete Excel archive file records + physical files
        files = ExcelFile.query.filter_by(station_id=station_id).all()
        deleted_files = 0
        for f in files:
            try:
                if os.path.exists(f.file_path):
                    os.remove(f.file_path)
            except Exception:
                pass
            MigrationHistory.query.filter_by(file_id=f.file_id).delete(synchronize_session=False)
            db.session.delete(f)
            deleted_files += 1

        # 2. Delete DataQualityIssue rows that reference observations for this station
        #    (must come before deleting observations due to FK constraint)
        DataQualityIssue.query.filter_by(station_id=station_id).delete(synchronize_session=False)

        # 3. Also catch any quality issues linked via observation_id / daily_observation_id
        obs_ids = db.session.query(Observation.observation_id).filter_by(station_id=station_id).subquery()
        daily_ids = db.session.query(DailyObservation.observation_id).filter_by(station_id=station_id).subquery()
        DataQualityIssue.query.filter(
            DataQualityIssue.observation_id.in_(obs_ids)
        ).delete(synchronize_session=False)
        DataQualityIssue.query.filter(
            DataQualityIssue.daily_observation_id.in_(daily_ids)
        ).delete(synchronize_session=False)

        # 4. Delete all monthly and daily observations for the station
        deleted_obs = Observation.query.filter_by(station_id=station_id).delete(synchronize_session=False)
        deleted_daily = DailyObservation.query.filter_by(station_id=station_id).delete(synchronize_session=False)

        db.session.commit()

        flash(
            f"Successfully purged all data for {station.station_name}: "
            f"{deleted_files} file record(s), {deleted_obs} monthly observation(s), "
            f"and {deleted_daily} daily observation(s) removed.",
            "success"
        )

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        flash(f"Error deleting data for {station.station_name}: {str(e)}", "danger")

    return redirect(url_for('excel_archive.index'))

