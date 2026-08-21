# Weather Data Management System (WDMS)

**Regional Meteorological Centre (RMC)**  
**Indian Meteorological Department (IMD)**  
**Chennai, Tamil Nadu**

---

## Overview

The Weather Data Management System is a production-grade application designed to centralize, manage, and analyze climatological data for approximately 16 meteorological stations across Tamil Nadu. The system replaces manual Excel-based workflows with a robust, database-driven solution.

## Features

### Core Functionality
- ✅ **Centralized Database**: PostgreSQL-based storage for all meteorological data
- ✅ **Data Migration**: Import historical data from Excel workbooks (1983-present)
- ✅ **Advanced Search**: Multi-criteria search (station, parameter, year, month, date range)
- ✅ **Data Entry**: Web-based forms with validation and duplicate prevention
- ✅ **Quality Control**: Automatic detection of missing values, outliers, and anomalies
- ✅ **Reporting**: Generate PDF, Excel, and CSV reports
- ✅ **Visualization**: Interactive charts and trend analysis
- ✅ **Excel Archive**: Browse and compare original Excel files
- ✅ **Security**: Role-based access control with audit logging
- ✅ **Backup & Recovery**: Automated PostgreSQL backups

### User Roles
1. **System Administrator**: Full system access, user management, configuration
2. **Meteorological Officer**: Data validation, reporting, analysis
3. **Data Entry Operator**: Enter new observations, limited access
4. **Read-Only User**: View data and generate reports only

---

## Technology Stack

### Backend
- **Python 3.9+**: Core application language
- **Flask 2.3+**: Web framework
- **SQLAlchemy 2.0+**: ORM for database interactions
- **PostgreSQL 14+**: Relational database
- **Pandas**: Data processing and analysis
- **OpenPyXL**: Excel file processing

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **DataTables**: Advanced table features
- **Chart.js**: Data visualization
- **jQuery**: DOM manipulation

### Additional Libraries
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing
- **ReportLab**: PDF generation
- **psycopg2**: PostgreSQL adapter

---

## Installation

### Prerequisites
1. **Python 3.9 or higher**
2. **PostgreSQL 14 or higher**
3. **Windows 10/11** (or compatible OS)

### Step 1: Clone or Extract Project
```bash
cd C:\Users\kavin\Desktop\imd
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure PostgreSQL

1. **Install PostgreSQL** from https://www.postgresql.org/download/windows/

2. **Create Database**:
```sql
-- Open pgAdmin or psql
CREATE DATABASE wdms_db;
CREATE USER wdms_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE wdms_db TO wdms_user;
```

3. **Update Configuration**:
Edit `config.py` and set your database credentials:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://wdms_user:your_password@localhost:5432/wdms_db'
```

### Step 5: Initialize Database
```bash
python init_db.py
```

This will:
- Create all database schemas and tables
- Insert default roles
- Create default admin user (username: `admin`, password: `admin123`)

### Step 6: Run Application
```bash
python run.py
```

Access the application at: **http://localhost:5000**

---

## Project Structure

```
imd/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── models.py                # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   ├── dashboard.py         # Dashboard routes
│   │   ├── data_entry.py        # Data entry routes
│   │   ├── search.py            # Search routes
│   │   ├── reports.py           # Report generation
│   │   ├── visualize.py         # Data visualization
│   │   ├── admin.py             # Admin panel
│   │   └── excel_archive.py     # Excel file viewer
│   ├── services/
│   │   ├── __init__.py
│   │   ├── station_service.py   # Station operations
│   │   ├── parameter_service.py # Parameter operations
│   │   ├── observation_service.py # Observation CRUD
│   │   ├── data_quality_service.py # Quality checks
│   │   ├── etl_service.py       # Excel migration
│   │   └── export_service.py    # Data export
│   ├── templates/               # Jinja2 HTML templates
│   ├── static/                  # CSS, JS, images
│   └── utils/                   # Utility functions
├── migrations/                  # Database migrations
├── backups/                     # Database backups
├── excel_archive/               # Original Excel files
├── exports/                     # Generated exports
├── logs/                        # Application logs
├── config.py                    # Configuration settings
├── init_db.py                   # Database initialization
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Usage Guide

### First Login
1. Navigate to http://localhost:5000
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. **Change password immediately** in Admin Panel > Profile

### Data Migration (Historical Data)

1. **Prepare Excel Files**:
   - Place Excel workbooks in `excel_archive/` directory
   - Naming convention: `STATION_CODE-MAST.xls` (e.g., `ARP-MAST.xls`)

2. **Configure Stations**:
   - Go to Admin Panel > Manage Stations
   - Add all stations with codes matching Excel filenames

3. **Configure Parameters**:
   - Go to Admin Panel > Manage Parameters
   - Add all meteorological parameters

4. **Run Migration**:
   - Go to Admin Panel > Data Migration
   - Select Excel file
   - Click "Migrate Data"
   - Monitor progress and review errors

### Daily Data Entry

1. Navigate to **Data Entry** menu
2. Select:
   - Station
   - Parameter
   - Year
   - Month
3. Enter value
4. Click **Save**
5. System validates and prevents duplicates

### Searching Data

1. Navigate to **Search** menu
2. Apply filters:
   - Station(s)
   - Parameter(s)
   - Date range
3. Click **Search**
4. Results displayed in table
5. Export to Excel/CSV if needed

### Generating Reports

1. Navigate to **Reports** menu
2. Choose report type:
   - Monthly Summary
   - Yearly Summary
   - Station Report
   - Parameter Trend
3. Select criteria
4. Click **Generate**
5. Download PDF/Excel

### Data Visualization

1. Navigate to **Visualize** menu
2. Select:
   - Station
   - Parameter
   - Date range
3. Choose chart type:
   - Line chart (trends)
   - Bar chart (comparisons)
4. View interactive chart
5. Download chart image

---

## Data Quality Features

### Automatic Detection
- ✅ Missing values (NULL, ***, blank cells)
- ✅ Trace values (TR, trace)
- ✅ Outliers (values outside valid range)
- ✅ Duplicate records
- ✅ Format errors (e.g., "25..3" instead of "25.3")
- ✅ Missing years/months

### Quality Dashboard
- View all quality issues
- Filter by severity (High/Medium/Low)
- Resolve or acknowledge issues
- Generate quality reports

---

## Security Features

### Authentication
- Secure password hashing (Werkzeug)
- Session management
- Login attempt limiting (5 attempts)
- Account lockout (30 minutes)

### Authorization
- Role-based access control (RBAC)
- Permission checks on every route
- Audit logging for all actions

### Audit Trail
- Who created/modified data
- When changes occurred
- What was changed (old vs new values)
- IP address and user agent logging

---

## Backup & Recovery

### Automatic Backups
Backups run daily at 2:00 AM:
```bash
python backup_db.py
```

### Manual Backup
```bash
python backup_db.py --manual
```

### Restore from Backup
```bash
psql -U wdms_user -d wdms_db < backups/backup_YYYYMMDD_HHMMSS.sql
```

---

## Troubleshooting

### Issue: Database Connection Error
**Solution**: 
- Check PostgreSQL is running
- Verify credentials in `config.py`
- Test connection: `psql -U wdms_user -d wdms_db`

### Issue: Port 5000 Already in Use
**Solution**: 
- Change port in `run.py`: `app.run(port=5001)`
- Or kill process using port 5000

### Issue: Excel Migration Fails
**Solution**:
- Check Excel file format
- Ensure station exists in database
- Review error log in migration report

### Issue: Slow Queries
**Solution**:
- Check database indexes: `python manage.py check_indexes`
- Run VACUUM: `VACUUM ANALYZE;`
- Consider partitioning observations table

---

## Maintenance

### Daily Tasks
- Monitor application logs: `logs/app.log`
- Check data quality dashboard
- Verify backup completion

### Weekly Tasks
- Review audit logs
- Check disk space
- Update data completeness statistics

### Monthly Tasks
- Database vacuum and analyze
- Archive old logs
- Review user accounts

---

## API Documentation

### REST API Endpoints

#### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout

#### Observations
- `GET /api/observations` - List observations (with filters)
- `POST /api/observations` - Create observation
- `PUT /api/observations/<id>` - Update observation
- `DELETE /api/observations/<id>` - Delete observation

#### Stations
- `GET /api/stations` - List all stations
- `GET /api/stations/<id>` - Get station details

#### Parameters
- `GET /api/parameters` - List all parameters
- `GET /api/parameters/<id>` - Get parameter details

#### Reports
- `POST /api/reports/generate` - Generate report

---

## Future Enhancements

### Phase 2 (Planned)
- [ ] AI/ML forecasting module
- [ ] Mobile application
- [ ] Real-time data ingestion
- [ ] Advanced anomaly detection
- [ ] Multi-language support
- [ ] RESTful API for external systems
- [ ] WebSocket for real-time updates

---

## Support

### Contact
- **Technical Support**: techsupport@imd.gov.in
- **Department**: Regional Meteorological Centre, Chennai
- **Phone**: +91-44-XXXX-XXXX

### Documentation
- User Manual: `docs/user_manual.pdf`
- Admin Guide: `docs/admin_guide.pdf`
- API Reference: `docs/api_reference.pdf`

---

## License

© 2024 Indian Meteorological Department, Government of India  
All Rights Reserved

This software is developed for internal use by IMD Chennai and is not licensed for external distribution.

---

## Change Log

### Version 1.0.0 (2024-XX-XX)
- Initial release
- Core data management features
- Excel migration tool
- Search and reporting
- Data quality module
- User authentication and authorization

---

**Built with ❤️ for IMD Chennai**
