# Weather Data Management System - Installation Guide

## Prerequisites

### Required Software
1. **Python 3.9 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **PostgreSQL 14 or higher**
   - Download from: https://www.postgresql.org/download/windows/
   - Remember the password you set for the postgres user

3. **Git** (optional, for version control)
   - Download from: https://git-scm.com/downloads

## Step-by-Step Installation

### Step 1: Extract Project Files

Extract the project to a folder, for example:
```
C:\Users\kavin\Desktop\imd\
```

### Step 2: Open Command Prompt

1. Press `Win + R`
2. Type `cmd` and press Enter
3. Navigate to project folder:
```cmd
cd C:\Users\kavin\Desktop\imd
```

### Step 3: Create Virtual Environment

```cmd
python -m venv venv
```

### Step 4: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your command prompt.

### Step 5: Install Python Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required Python packages. It may take 2-5 minutes.

### Step 6: Configure PostgreSQL

#### 6.1 Open pgAdmin or psql

**Option A: Using pgAdmin (GUI)**
1. Open pgAdmin from Start Menu
2. Connect to your PostgreSQL server
3. Right-click on "Databases" → "Create" → "Database"

**Option B: Using psql (Command Line)**
1. Open Command Prompt
2. Run: `psql -U postgres`
3. Enter your postgres password

#### 6.2 Create Database

Execute these SQL commands:

```sql
-- Create database
CREATE DATABASE wdms_db;

-- Create user
CREATE USER wdms_user WITH PASSWORD 'wdms_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wdms_db TO wdms_user;

-- Connect to the new database
\c wdms_db

-- Grant schema creation privilege
GRANT CREATE ON DATABASE wdms_db TO wdms_user;
```

**Important:** Change 'wdms_password' to a strong password!

### Step 7: Configure Application

Edit the `config.py` file and update the database connection:

```python
SQLALCHEMY_DATABASE_URI = 'postgresql://wdms_user:wdms_password@localhost:5432/wdms_db'
```

Replace `wdms_password` with the password you set in Step 6.2.

### Step 8: Initialize Database

```cmd
python init_db.py
```

You should see output like:
```
Creating database schemas...
  ✓ Schema 'core' created
  ✓ Schema 'security' created
  ...
✓ Database initialization completed successfully!
```

### Step 9: Run the Application

```cmd
python run.py
```

You should see:
```
==================================================
Weather Data Management System
Indian Meteorological Department - Chennai
==================================================
Server running on: http://0.0.0.0:5000
...
```

### Step 10: Access the Application

1. Open your web browser
2. Go to: `http://localhost:5000`
3. Login with default credentials:
   - **Username:** admin
   - **Password:** admin123

### Step 11: Change Admin Password

**IMPORTANT:** After first login:
1. Click on your name in top-right corner
2. Select "Change Password"
3. Enter a strong new password
4. Click "Change Password"

## Troubleshooting

### Error: "PostgreSQL service not running"
**Solution:** 
1. Press `Win + R`, type `services.msc`
2. Find "postgresql-x64-14" service
3. Right-click → Start

### Error: "Unable to connect to database"
**Solution:**
1. Check PostgreSQL is running (see above)
2. Verify username and password in `config.py`
3. Test connection using pgAdmin

### Error: "Port 5000 already in use"
**Solution:**
1. Edit `run.py`, change port to 5001:
   ```python
   app.run(host=host, port=5001, debug=debug)
   ```
2. Access at `http://localhost:5001`

### Error: "Module not found"
**Solution:**
1. Make sure virtual environment is activated:
   ```cmd
   venv\Scripts\activate
   ```
2. Reinstall requirements:
   ```cmd
   pip install -r requirements.txt
   ```

### Database initialization fails
**Solution:**
1. Drop and recreate database:
   ```sql
   DROP DATABASE IF EXISTS wdms_db;
   CREATE DATABASE wdms_db;
   GRANT ALL PRIVILEGES ON DATABASE wdms_db TO wdms_user;
   ```
2. Run init_db.py again

## Next Steps

After successful installation:

1. **Add Stations**
   - Go to Admin Panel → Manage Stations
   - Add all your meteorological stations

2. **Add Parameters**
   - Go to Admin Panel → Manage Parameters
   - Add all weather parameters you measure

3. **Enter Data**
   - Use Data Entry form to add observations
   - Or prepare for Excel migration

4. **Create Users**
   - Go to Admin Panel → Manage Users
   - Add users for your team with appropriate roles

## Production Deployment

For production deployment on a Windows Server:

1. **Install Gunicorn alternative (waitress)**
   ```cmd
   pip install waitress
   ```

2. **Create production runner (run_production.py)**
   ```python
   from waitress import serve
   from app import create_app
   app = create_app()
   serve(app, host='0.0.0.0', port=5000, threads=4)
   ```

3. **Run in production**
   ```cmd
   python run_production.py
   ```

4. **Set up Windows Service**
   - Use NSSM (Non-Sucking Service Manager)
   - Download from: https://nssm.cc/download
   - Install as service:
     ```cmd
     nssm install WDMS "C:\path\to\venv\Scripts\python.exe" "C:\path\to\run_production.py"
     nssm start WDMS
     ```

## Support

For issues or questions:
- Email: techsupport@imd.gov.in
- Phone: +91-44-XXXX-XXXX

## Security Checklist

Before going live:
- [ ] Changed default admin password
- [ ] Updated SECRET_KEY in config.py
- [ ] Set strong database password
- [ ] Enabled firewall rules
- [ ] Configured backup schedule
- [ ] Tested restore procedure
- [ ] Created user accounts
- [ ] Assigned appropriate roles
- [ ] Documented admin procedures

---

**Version:** 1.0  
**Last Updated:** June 2026
