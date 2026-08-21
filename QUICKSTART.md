# Quick Start Guide

## 5-Minute Setup (for Development/Testing)

### Prerequisites
- Python 3.9+ installed
- PostgreSQL 14+ installed and running

### Quick Installation

```cmd
# 1. Navigate to project folder
cd C:\Users\kavin\Desktop\imd

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create PostgreSQL database
psql -U postgres
```

In psql, run:
```sql
CREATE DATABASE wdms_db;
CREATE USER wdms_user WITH PASSWORD 'wdms_password';
GRANT ALL PRIVILEGES ON DATABASE wdms_db TO wdms_user;
\c wdms_db
GRANT CREATE ON DATABASE wdms_db TO wdms_user;
\q
```

```cmd
# 5. Initialize database
python init_db.py

# 6. Run application
python run.py
```

### Access Application

1. Open browser: `http://localhost:5000`
2. Login: **admin** / **admin123**
3. Change password immediately!

---

## Common Tasks

### Add a New Station
1. Login as admin
2. Admin Panel → Manage Stations
3. Currently view-only; use database or add via admin interface

**SQL Method:**
```sql
INSERT INTO core.stations (station_code, station_name, district, state, is_active)
VALUES ('MDU', 'Madurai', 'Madurai', 'Tamil Nadu', true);
```

### Add a New Parameter
1. Admin Panel → Manage Parameters
2. Currently view-only; use database

**SQL Method:**
```sql
INSERT INTO core.parameters (
    parameter_code, parameter_name, unit, category, 
    data_type, min_value, max_value, decimal_places, 
    aggregation_type, display_order, is_active
)
VALUES (
    'TEMP_MEAN', 'Mean Temperature', 'DEG C', 'TEMPERATURE',
    'NUMERIC', -10.0, 50.0, 1, 'MEAN', 10, true
);
```

### Enter Observation Data
1. Data Entry → Data Entry
2. Select: Station, Parameter, Year, Month
3. Enter value
4. Click "Save Observation"

### Search for Data
1. Search Data
2. Select filters (Station, Parameter, Year range)
3. Click "Search"
4. View results in table

### Export Data to CSV
1. Reports → Export Data
2. Select filters
3. Click "Export to CSV"
4. File downloads automatically

### View Charts
1. Visualize
2. Select: Station, Parameter, Year range
3. Click "Generate Chart"
4. Interactive line chart appears

---

## User Roles

### ADMIN
- **Username:** admin
- **Default Password:** admin123
- **Permissions:** Full system access
- **Can:** Manage users, stations, parameters, view all data

### MET_OFFICER
- **Permissions:** Read, Write, Approve, Report
- **Can:** Enter data, generate reports, validate observations

### DATA_ENTRY
- **Permissions:** Read, Write
- **Can:** Enter and edit observation data

### READ_ONLY
- **Permissions:** Read only
- **Can:** Search and view data, generate reports

---

## Sample Workflow

### Daily Data Entry
1. Login as DATA_ENTRY user
2. Go to Data Entry
3. Select your station
4. Enter today's readings for all parameters
5. Logout

### Monthly Report Generation
1. Login as MET_OFFICER
2. Go to Reports
3. Select station and month
4. Export to CSV or PDF
5. Review and approve data

### Data Analysis
1. Login with any role
2. Go to Visualize
3. Select parameter and date range
4. Analyze trends
5. Export chart if needed

---

## Keyboard Shortcuts (Future Enhancement)

- **Ctrl+K:** Quick search
- **Ctrl+E:** Export current view
- **Ctrl+N:** New data entry
- **Ctrl+S:** Save form

---

## Tips & Best Practices

### Data Entry
✅ **DO:**
- Enter data daily
- Use TR for trace amounts
- Use *** for missing data
- Add remarks for unusual values
- Double-check before saving

❌ **DON'T:**
- Leave fields blank without marking as missing
- Enter estimated values without noting in remarks
- Modify historical data without authorization

### Data Quality
- Review Data Quality Dashboard weekly
- Resolve HIGH priority issues immediately
- Investigate MEDIUM priority issues monthly
- Document all data corrections

### Security
- Change default passwords immediately
- Use strong passwords (8+ characters, mixed case, numbers)
- Logout when done
- Don't share accounts
- Report suspicious activity

---

## Troubleshooting Quick Fixes

### Can't Login
- Check username spelling
- Try password reset (contact admin)
- Verify account is active

### Data Not Saving
- Check all required fields filled
- Verify value is in valid range
- Look for error messages
- Try refreshing page

### Slow Performance
- Close other applications
- Clear browser cache
- Check network connection
- Contact IT if persists

### Chart Not Loading
- Verify data exists for selected criteria
- Try smaller date range
- Refresh browser
- Check JavaScript enabled

---

## Getting Help

### In-App Help
- Hover over (i) icons for tooltips
- Read instructions on each page
- Check alert messages

### Documentation
- README.md - Overview
- INSTALL.md - Installation details
- ARCHITECTURE_REVIEW.md - Technical details

### Contact Support
- **Email:** techsupport@imd.gov.in
- **Phone:** +91-44-XXXX-XXXX
- **Office Hours:** Mon-Fri 9AM-5PM

---

## Next Steps After Quickstart

1. **Explore the Interface**
   - Try all menu items
   - Enter sample data
   - Generate a test report

2. **Set Up Your Stations**
   - Add all meteorological stations
   - Verify station details

3. **Configure Parameters**
   - Add all parameters you measure
   - Set appropriate ranges

4. **Create User Accounts**
   - One account per person
   - Assign appropriate roles
   - Document credentials securely

5. **Plan Data Migration**
   - Inventory Excel files
   - Test migration with one file
   - Schedule full migration

6. **Train Your Team**
   - Conduct hands-on training
   - Create internal procedures
   - Designate system administrator

---

**Happy Data Management!** 📊☁️🌡️

*Indian Meteorological Department, Chennai*
