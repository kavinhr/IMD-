import os
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from app.models import Station, Parameter, WordDocExtremeData
from app import db
from datetime import datetime

import_extreme_bp = Blueprint('import_extreme', __name__)

MONTHS_MAP = {
    'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
    'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8,
    'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
}

def iter_block_items(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def clean_dt(dt_str):
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    if dt_str in ['-', '', ',', 'None', 'N/A']:
        return None
    return dt_str

def resolve_station(name):
    if not name:
        return None
    name_clean = re.sub(r'[\(\)\.\,\-_]', ' ', name).strip()
    name_clean = re.sub(r'\s+', ' ', name_clean).upper()
    
    aliases = {
        'CHENNAI N': 'Chennai (Nungambakkam)',
        'CHENNAI NUNGAMBAKKAM': 'Chennai (Nungambakkam)',
        'NUNGAMBAKKAM': 'Chennai (Nungambakkam)',
        'CHENNAI': 'Chennai (Nungambakkam)',
        'CHENNAI M': 'Chennai (Meenambakkam)',
        'CHENNAI MEENAMBAKKAM': 'Chennai (Meenambakkam)',
        'MEENAMBAKKAM': 'Chennai (Meenambakkam)',
        'MADURAI AP': 'Madurai Airport',
        'MADURAI AIRPORT': 'Madurai Airport',
        'MADURAI': 'Madurai Airport',
        'MADURAI AP OBSY': 'Madurai Airport',
        'TIRUCHIRAPALLI AP': 'Tiruchirapalli Airport',
        'TIRUCHIRAPPALLI AP': 'Tiruchirapalli Airport',
        'TIRUCHIRAPALLI AIRPORT': 'Tiruchirapalli Airport',
        'TIRUCHIRAPPALLI AIRPORT': 'Tiruchirapalli Airport',
        'TIRUCHIRAPALLI': 'Tiruchirapalli Airport',
        'TIRUCHIRAPPALLI': 'Tiruchirapalli Airport',
        'TRICHY AP': 'Tiruchirapalli Airport',
        'TRICHY AIRPORT': 'Tiruchirapalli Airport',
        'TRICHY': 'Tiruchirapalli Airport',
        'COIMBATORE AP': 'Coimbatore Airport',
        'COIMBATORE AIRPORT': 'Coimbatore Airport',
        'COIMBATORE': 'Coimbatore Airport',
        'SALEM': 'Salem',
        'SALEM OBSY': 'Salem',
        'SALEM SO': 'Salem',
        'SALEM AP': 'Salem',
        'SALEM AIRPORT': 'Salem',
        'PUDUCHERRY': 'Puducherry',
        'PUDUCHERRY OBSY': 'Puducherry',
        'PONDICHERRY': 'Puducherry',
        'PONDICHERRY OBSY': 'Puducherry',
        'ADIRAMPATTINAM': 'Adirampattinam',
        'ADIRAMPATTINAM OBSY': 'Adirampattinam',
        'TONDI': 'Tondi',
        'TONDI OBSY': 'Tondi',
        'CUDDALORE': 'Cuddalore',
        'CUDDALORE OBSY': 'Cuddalore',
        'CUDDALORE MP': 'Cuddalore',
        'KODAIKANAL': 'Kodaikanal',
        'KODAIKANAL OBSY': 'Kodaikanal',
        'KANYAKUMARI': 'Kanyakumari',
        'KANYAKUMARI OBSY': 'Kanyakumari',
        'NAGAPATTINAM': 'Nagapattinam',
        'NAGAPATTINAM OBSY': 'Nagapattinam',
        'VELLORE': 'Vellore',
        'VELLORE OBSY': 'Vellore',
        'KARAIKAL': 'Karaikal',
        'KARAIKAL OBSY': 'Karaikal',
        'PAMBAN': 'Pamban',
        'PAMBAN OBSY': 'Pamban'
    }
    
    if name_clean in aliases:
        target = aliases[name_clean]
        station = Station.query.filter(Station.station_name.ilike(target)).first()
        if station:
            return station
            
    for k, target in aliases.items():
        if len(k) >= 4 and (k in name_clean or name_clean in k):
            station = Station.query.filter(Station.station_name.ilike(target)).first()
            if station:
                return station

    # Exact case insensitive match
    station = Station.query.filter(db.func.upper(Station.station_name) == name.strip().upper()).first()
    if station:
        return station
        
    # ilike match
    station = Station.query.filter(Station.station_name.ilike(f"%{name.strip()}%")).first()
    if station:
        return station

    # Check against all active stations by cleaning names
    all_stations = Station.query.filter_by(is_active=True).all()
    for st in all_stations:
        st_clean = re.sub(r'[\(\)\.\,\-_]', ' ', st.station_name).strip()
        st_clean = re.sub(r'\s+', ' ', st_clean).upper()
        if st_clean == name_clean:
            return st
            
    # Remove common suffixes and compare core words
    words_to_remove = {'AP', 'AIRPORT', 'OBSY', 'OBSERVATORY', 'SO', 'MP', 'MO', 'STATION'}
    name_words = [w for w in name_clean.split() if w not in words_to_remove]
    if name_words:
        core_name = " ".join(name_words)
        for st in all_stations:
            st_clean = re.sub(r'[\(\)\.\,\-_]', ' ', st.station_name).strip()
            st_clean = re.sub(r'\s+', ' ', st_clean).upper()
            st_words = [w for w in st_clean.split() if w not in words_to_remove]
            if st_words and " ".join(st_words) == core_name:
                return st

    return None

def extract_val_date(text):
    if not text or text.strip() == '-' or text.strip() == '':
        return None, None
        
    text = text.replace('\n', ' ').strip()
    match = re.match(r'^([\-\d\.]+)\s*(?:\(\s*([^)]+)\s*\))?$', text)
    if match:
        val = float(match.group(1))
        dt = clean_dt(match.group(2))
        return val, dt
        
    try:
        return float(text), None
    except:
        return None, None

def extract_val_date_year(text):
    if not text or text.strip() == '-' or text.strip() == '':
        return None, None, None
        
    text = text.replace('\n', ' ').strip()
    # Matches: VALUE (DATE, YEAR) or VALUE (YEAR) or VALUE (-, YEAR)
    match = re.match(r'^([\-\d\.]+)\s*(?:\(\s*([^)]+)\s*\))?$', text)
    if match:
        val = float(match.group(1))
        inner = match.group(2)
        if inner:
            parts = [p.strip() for p in inner.split(',')]
            if len(parts) >= 2:
                last_part = parts[-1]
                if last_part.isdigit() and len(last_part) == 4:
                    yr = int(last_part)
                    dt_parts = [p for p in parts[:-1] if p and p != '-']
                    dt = clean_dt(", ".join(dt_parts)) if dt_parts else None
                    return val, dt, yr
                else:
                    dt = clean_dt(inner)
                    return val, dt, None
            elif len(parts) == 1:
                if parts[0].isdigit() and len(parts[0]) == 4:
                    return val, None, int(parts[0])
                else:
                    dt = clean_dt(parts[0])
                    return val, dt, None
        return val, None, None
        
    return None, None, None

def upsert_word_doc_extreme(station_id, month, year, param_id, val, dt=None):
    if val is None:
        return 0
    dt = clean_dt(dt)
        
    obs = WordDocExtremeData.query.filter_by(
        station_id=station_id,
        obs_month=month,
        obs_year=year,
        parameter_id=param_id
    ).first()
    
    updated = False
    if not obs:
        obs = WordDocExtremeData(
            station_id=station_id,
            parameter_id=param_id,
            obs_year=year,
            obs_month=month,
            obs_value=val,
            date_of_extreme=dt
        )
        db.session.add(obs)
        updated = True
    else:
        if float(obs.obs_value) != float(val) or obs.date_of_extreme != dt:
            obs.obs_value = val
            obs.date_of_extreme = dt
            obs.updated_at = datetime.utcnow()
            updated = True
            
    return 1 if updated else 0

@import_extreme_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if not current_user.has_permission('write'):
        flash('You do not have permission to access this feature.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        files = request.files.getlist('file')
        if not files or all(f.filename == '' for f in files):
            flash('No file selected.', 'warning')
            return redirect(request.url)
            
        import tempfile
        import os
        import win32com.client
        import pythoncom
        
        p_tmax = Parameter.query.filter_by(parameter_code='TEMP_MAX_HIGH').first()
        p_tmin = Parameter.query.filter_by(parameter_code='TEMP_MIN_LOW').first()
        p_rf24 = Parameter.query.filter_by(parameter_code='RAINFALL_MAX_24HR').first()
        p_rfm = Parameter.query.filter_by(parameter_code='RAINFALL_TOTAL').first()
        
        if not all([p_tmax, p_tmin, p_rf24, p_rfm]):
            flash('Missing parameters in the database.', 'danger')
            return redirect(request.url)
            
        total_stations_processed = 0
        total_records_updated = 0
        
        has_doc = any(f.filename and f.filename.endswith('.doc') for f in files)
        word_app = None
        
        if has_doc:
            pythoncom.CoInitialize()
            try:
                word_app = win32com.client.Dispatch('Word.Application')
                word_app.Visible = False
                word_app.DisplayAlerts = False
            except Exception as e:
                flash(f"Failed to initialize document converter: {str(e)}", "danger")
                return redirect(request.url)
        
        try:
            for file in files:
                if file.filename == '':
                    continue
                    
                if not (file.filename.endswith('.docx') or file.filename.endswith('.doc')):
                    flash(f'Skipped {file.filename}: Invalid format. Please upload .doc or .docx.', 'warning')
                    continue
                
                try:
                    temp_dir = tempfile.gettempdir()
                    doc_to_read = file
                    temp_doc = None
                    temp_docx = None
                    
                    if file.filename.endswith('.doc') and word_app:
                        # Save the uploaded .doc file
                        temp_doc = os.path.join(temp_dir, f"temp_upload_{os.urandom(4).hex()}.doc")
                        temp_docx = os.path.join(temp_dir, f"temp_upload_{os.urandom(4).hex()}.docx")
                        file.save(temp_doc)
                        
                        # Convert .doc to .docx
                        doc_obj = word_app.Documents.Open(temp_doc)
                        doc_obj.SaveAs2(temp_docx, FileFormat=16) # 16 = wdFormatXMLDocument (.docx)
                        doc_obj.Close()
                        
                        doc_to_read = temp_docx
                        
                    doc = Document(doc_to_read)
                    
                    # Clean up temp files if we converted
                    if temp_doc and os.path.exists(temp_doc):
                        try: os.remove(temp_doc)
                        except: pass
                    if temp_docx and os.path.exists(temp_docx):
                        try: os.remove(temp_docx)
                        except: pass
                
                    current_station_name = None
                    current_month_name = None
                
                    for block in iter_block_items(doc):
                        if isinstance(block, Paragraph):
                            text = ''.join([t.text for t in block._element.xpath('.//w:t') if t.text]).strip()
                            if not text:
                                continue
                            
                            month_match = re.search(r'MONTH OF\s+([A-Z]+)', text.upper())
                            if month_match:
                                current_month_name = month_match.group(1).strip()
                            else:
                                st_match = re.match(r'^\d+\s*\.\s*(.+)$', text)
                                if st_match:
                                    current_station_name = st_match.group(1).strip().upper()
                                
                        elif isinstance(block, Table):
                            if current_station_name and current_month_name:
                                # Find station using resolve_station
                                station = resolve_station(current_station_name)
                                
                                month_num = MONTHS_MAP.get(current_month_name)
                            
                                if station and month_num:
                                    total_stations_processed += 1
                                    # Parse table
                                    for row in block.rows[2:]:
                                        cells = [''.join([t.text for t in c._element.xpath('.//w:t') if t.text]).strip() for c in row.cells]
                                        if len(cells) < 5:
                                            continue
                                        
                                        year_str = cells[0].replace('\n', ' ').strip()
                                    
                                        if 'ALL TIME' in year_str.upper():
                                            # Process ATR
                                            tmax_v, tmax_d, tmax_y = extract_val_date_year(cells[1])
                                            tmin_v, tmin_d, tmin_y = extract_val_date_year(cells[2])
                                            rf24_v, rf24_d, rf24_y = extract_val_date_year(cells[3])
                                        
                                            # Monthly Total usually just has year
                                            rfm_v, _, rfm_y = extract_val_date_year(cells[4])
                                        
                                            if tmax_y: total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, tmax_y, p_tmax.parameter_id, tmax_v, tmax_d)
                                            if tmin_y: total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, tmin_y, p_tmin.parameter_id, tmin_v, tmin_d)
                                            if rf24_y: total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, rf24_y, p_rf24.parameter_id, rf24_v, rf24_d)
                                            if rfm_y: total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, rfm_y, p_rfm.parameter_id, rfm_v)
                                        else:
                                            try:
                                                year = int(year_str)
                                                tmax_v, tmax_d = extract_val_date(cells[1])
                                                tmin_v, tmin_d = extract_val_date(cells[2])
                                                rf24_v, rf24_d = extract_val_date(cells[3])
                                                rfm_v, _ = extract_val_date(cells[4])
                                            
                                                total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, year, p_tmax.parameter_id, tmax_v, tmax_d)
                                                total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, year, p_tmin.parameter_id, tmin_v, tmin_d)
                                                total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, year, p_rf24.parameter_id, rf24_v, rf24_d)
                                                total_records_updated += upsert_word_doc_extreme(station.station_id, month_num, year, p_rfm.parameter_id, rfm_v)
                                            except ValueError:
                                                pass
                                    db.session.commit()
                            
                                current_station_name = None
                                current_month_name = None
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error processing file {file.filename}: {str(e)}', 'danger')

        finally:
            if word_app:
                try:
                    word_app.Quit()
                except:
                    pass
                pythoncom.CoUninitialize()

        if total_records_updated > 0:
            flash(f'Successfully processed {total_stations_processed} station blocks across documents. Inserted/Updated {total_records_updated} observation records.', 'success')
        return redirect(url_for('import_extreme.index'))
            
    # Fetch uploaded months for the table
    uploaded_months_raw = db.session.query(WordDocExtremeData.obs_month).distinct().all()
    uploaded_months = [m[0] for m in uploaded_months_raw if m[0] is not None]
    
    return render_template('reports/import_extreme.html', uploaded_months=uploaded_months, months_map=MONTHS_MAP)

@import_extreme_bp.route('/delete/<int:month>', methods=['POST'])
@login_required
def delete_month(month):
    if not current_user.has_permission('delete'):
        flash('You do not have permission to delete records.', 'danger')
        return redirect(url_for('import_extreme.index'))
        
    try:
        deleted = WordDocExtremeData.query.filter_by(obs_month=month).delete()
        db.session.commit()
        
        month_name = "Unknown"
        for name, num in MONTHS_MAP.items():
            if num == month:
                month_name = name
                break
                
        flash(f'Successfully deleted {deleted} extreme records for {month_name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting records: {str(e)}', 'danger')
        
    return redirect(url_for('import_extreme.index'))
