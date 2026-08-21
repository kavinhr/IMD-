# PostgreSQL Installation and Setup Guide

## Step 1: Download PostgreSQL

1. Visit: **https://www.postgresql.org/download/windows/**
2. Click **"Download the installer"** (EnterpriseDB)
3. Download **PostgreSQL 16** or **PostgreSQL 15** (latest stable version)

## Step 2: Install PostgreSQL

1. Run the downloaded `.exe` installer file
2. Follow the installation wizard:
   - Installation Directory: `C:\Program Files\PostgreSQL\16\` (default)
   - Select Components: Install all (PostgreSQL Server, pgAdmin, Command Line Tools)
   - Data Directory: Default location
   - **IMPORTANT**: Set a password for the `postgres` superuser
     - **Remember this password!** You'll need it later
     - Example: `postgres123` (change in production!)
   - Port: `5432` (default)
   - Locale: Default
3. Click **Next** and **Install**
4. When asked about Stack Builder, click **Finish** (not needed)

## Step 3: Verify Installation

Open a **NEW** PowerShell window (to load updated PATH) and run:

```powershell
psql --version
```

You should see output like: `psql (PostgreSQL) 16.x`

If not found, add to PATH manually:
- Search "Environment Variables" in Windows
- Edit System PATH
- Add: `C:\Program Files\PostgreSQL\16\bin`
- Restart PowerShell

## Step 4: Create Database and User

Open PowerShell and run:

```powershell
# Connect to PostgreSQL as postgres user
# Enter the password you set during installation
psql -U postgres
```

In the PostgreSQL prompt (`postgres=#`), run these SQL commands:

```sql
-- Create the database
CREATE DATABASE wdms_db;

-- Create the user
CREATE USER wdms_user WITH PASSWORD 'wdms_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wdms_db TO wdms_user;

-- Grant schema privileges
\c wdms_db
GRANT ALL ON SCHEMA public TO wdms_user;

-- Exit
\q
```

## Step 5: Initialize the Application Database

Navigate to your project directory and run:

```powershell
cd C:\Users\kavin\Desktop\imd
.\venv\Scripts\python.exe init_db.py
```

This will:
- Create all schemas (core, security, quality, archive, audit)
- Create all database tables
- Insert default roles
- Create admin user (admin/admin123)
- Insert sample stations and parameters

## Step 6: Start the Application

```powershell
.\venv\Scripts\python.exe run.py
```

## Step 7: Access the Application

Open your browser and navigate to:
- **http://localhost:5000**

Login with:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

---

## Configuration Details

The application is now configured with:

**Database Connection String:**
```
postgresql://wdms_user:wdms_password@localhost:5432/wdms_db
```

**Configuration Location:** `config.py`

**Database Schemas:**
- `security` - Users, roles, authentication
- `core` - Stations, parameters, observations
- `quality` - Data quality tracking
- `archive` - Excel files, migration history
- `audit` - Audit logs

---

## Troubleshooting

### Problem: "psql: command not found"
**Solution**: PostgreSQL is not installed or not in PATH. Reinstall or add to PATH manually.

### Problem: "password authentication failed"
**Solution**: Check your postgres password. Reset it:
```sql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### Problem: "database wdms_db does not exist"
**Solution**: Run the CREATE DATABASE command from Step 4.

### Problem: "permission denied for schema"
**Solution**: Grant permissions:
```sql
\c wdms_db
GRANT ALL ON SCHEMA public TO wdms_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO wdms_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO wdms_user;
```

### Problem: "could not connect to server"
**Solution**: Ensure PostgreSQL service is running:
- Open Services (services.msc)
- Find "postgresql-x64-16" (or your version)
- Ensure it's "Running"
- If not, right-click and "Start"

---

## Production Recommendations

When deploying to production:

1. **Change default passwords**:
   - Admin user password
   - Database user password (wdms_user)
   - Postgres superuser password

2. **Update config.py**:
   - Set `DEBUG = False`
   - Use strong `SECRET_KEY`
   - Enable `SESSION_COOKIE_SECURE = True` with HTTPS

3. **Use a production WSGI server**:
   - Install: `pip install gunicorn` (Linux) or `pip install waitress` (Windows)
   - Run: `waitress-serve --port=5000 run:app`

4. **Set up regular backups**:
   ```powershell
   pg_dump -U wdms_user -d wdms_db > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
   ```

5. **Configure PostgreSQL for production**:
   - Adjust `postgresql.conf` settings
   - Set up connection pooling
   - Configure pg_hba.conf for security

---

## Uninstalling PostgreSQL (if needed)

1. Open Control Panel → Programs and Features
2. Find "PostgreSQL 16" (or your version)
3. Click Uninstall
4. Manually delete data directory if prompted:
   - Default: `C:\Program Files\PostgreSQL\16\data`

---

## Need Help?

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- pgAdmin (GUI tool): Installed with PostgreSQL
- Check logs: `C:\Program Files\PostgreSQL\16\data\log\`
