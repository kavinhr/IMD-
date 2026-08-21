import os
import glob
import re
import tempfile
from docx import Document
from app import create_app, db
from app.models import WordDocExtremeData, Station, Parameter
from app.routes.import_extreme import (
    iter_block_items, clean_dt, resolve_station, MONTHS_MAP,
    extract_val_date, extract_val_date_year, upsert_word_doc_extreme, Paragraph, Table
)
import win32com.client
import pythoncom

def run_reimport():
    app = create_app()
    with app.app_context():
        p_tmax = Parameter.query.filter_by(parameter_code='TEMP_MAX_HIGH').first()
        p_tmin = Parameter.query.filter_by(parameter_code='TEMP_MIN_LOW').first()
        p_rf24 = Parameter.query.filter_by(parameter_code='RAINFALL_MAX_24HR').first()
        p_rfm = Parameter.query.filter_by(parameter_code='RAINFALL_TOTAL').first()

        folder = r'C:\Users\kavin\Desktop\10 year extremes'
        files = sorted(glob.glob(os.path.join(folder, '*.doc*')))
        files = [f for f in files if not os.path.basename(f).startswith('~$')]

        print(f"Found {len(files)} Word files to process.")

        pythoncom.CoInitialize()
        word_app = None
        try:
            word_app = win32com.client.Dispatch('Word.Application')
            word_app.Visible = False
            word_app.DisplayAlerts = False
        except Exception as e:
            print("Failed to dispatch Word:", e)
            return

        total_stations_processed = 0
        total_records_updated = 0

        try:
            for filepath in files:
                filename = os.path.basename(filepath)
                print(f"--- Processing {filename} ---")
                
                temp_dir = tempfile.gettempdir()
                doc_to_read = filepath
                temp_docx = None
                
                if filename.endswith('.doc'):
                    temp_docx = os.path.join(temp_dir, f"reimport_{os.urandom(4).hex()}.docx")
                    try:
                        doc_obj = word_app.Documents.Open(os.path.abspath(filepath))
                        doc_obj.SaveAs2(temp_docx, FileFormat=16)
                        doc_obj.Close()
                        doc_to_read = temp_docx
                    except Exception as e:
                        print(f"Error converting {filename}: {e}")
                        try: doc_obj.Close()
                        except: pass
                        continue
                
                try:
                    doc = Document(doc_to_read)
                except Exception as e:
                    print(f"Error reading docx for {filename}: {e}")
                    if temp_docx and os.path.exists(temp_docx):
                        try: os.remove(temp_docx)
                        except: pass
                    continue
                
                current_station_name = None
                current_month_name = None
                
                # Check if month is in filename as fallback
                for mstr in MONTHS_MAP.keys():
                    if re.search(r'\b' + mstr + r'\b', filename.upper()):
                        current_month_name = mstr
                        break

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
                            else:
                                st_match2 = re.match(r'^STATION[\:\s]+(.+)$', text, flags=re.IGNORECASE)
                                if st_match2:
                                    current_station_name = st_match2.group(1).strip().upper()
                                    
                    elif isinstance(block, Table):
                        if current_station_name and current_month_name:
                            station = resolve_station(current_station_name)
                            month_num = MONTHS_MAP.get(current_month_name)
                        
                            if station and month_num:
                                total_stations_processed += 1
                                st_records = 0
                                for row in block.rows[2:]:
                                    cells = [''.join([t.text for t in c._element.xpath('.//w:t') if t.text]).strip() for c in row.cells]
                                    if len(cells) < 5:
                                        continue
                                    
                                    year_str = cells[0].replace('\n', ' ').strip()
                                
                                    if 'ALL TIME' in year_str.upper():
                                        tmax_v, tmax_d, tmax_y = extract_val_date_year(cells[1])
                                        tmin_v, tmin_d, tmin_y = extract_val_date_year(cells[2])
                                        rf24_v, rf24_d, rf24_y = extract_val_date_year(cells[3])
                                        rfm_v, _, rfm_y = extract_val_date_year(cells[4])
                                    
                                        if tmax_y: st_records += upsert_word_doc_extreme(station.station_id, month_num, tmax_y, p_tmax.parameter_id, tmax_v, tmax_d)
                                        if tmin_y: st_records += upsert_word_doc_extreme(station.station_id, month_num, tmin_y, p_tmin.parameter_id, tmin_v, tmin_d)
                                        if rf24_y: st_records += upsert_word_doc_extreme(station.station_id, month_num, rf24_y, p_rf24.parameter_id, rf24_v, rf24_d)
                                        if rfm_y: st_records += upsert_word_doc_extreme(station.station_id, month_num, rfm_y, p_rfm.parameter_id, rfm_v)
                                    else:
                                        try:
                                            year = int(year_str)
                                            tmax_v, tmax_d = extract_val_date(cells[1])
                                            tmin_v, tmin_d = extract_val_date(cells[2])
                                            rf24_v, rf24_d = extract_val_date(cells[3])
                                            rfm_v, _ = extract_val_date(cells[4])
                                        
                                            st_records += upsert_word_doc_extreme(station.station_id, month_num, year, p_tmax.parameter_id, tmax_v, tmax_d)
                                            st_records += upsert_word_doc_extreme(station.station_id, month_num, year, p_tmin.parameter_id, tmin_v, tmin_d)
                                            st_records += upsert_word_doc_extreme(station.station_id, month_num, year, p_rf24.parameter_id, rf24_v, rf24_d)
                                            st_records += upsert_word_doc_extreme(station.station_id, month_num, year, p_rfm.parameter_id, rfm_v)
                                        except ValueError:
                                            pass
                                total_records_updated += st_records
                                print(f"  -> Imported {station.station_name} ({current_month_name}): {st_records} records")
                                db.session.commit()
                        
                        # reset after table if it was a 10 year table
                        # keep month name for next stations
                        current_station_name = None
                
                if temp_docx and os.path.exists(temp_docx):
                    try: os.remove(temp_docx)
                    except: pass

        finally:
            if word_app:
                try: word_app.Quit()
                except: pass
            pythoncom.CoUninitialize()

        print(f"\nDONE! Processed {total_stations_processed} station blocks across documents. Inserted/Updated {total_records_updated} observation records.")

if __name__ == '__main__':
    run_reimport()
