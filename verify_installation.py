"""
Installation Verification Script
Run this after installation to verify everything is working
"""
import sys
import os

def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_status(check, status, message=""):
    symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAIL"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {check}: {status_text} {message}")
    return status

def main():
    print_header("Weather Data Management System - Installation Verification")
    
    all_checks_passed = True
    
    # Check Python version
    print("\n[1] Checking Python Environment...")
    python_version = sys.version_info
    status = python_version.major == 3 and python_version.minor >= 9
    all_checks_passed &= print_status(
        "Python Version",
        status,
        f"(Found: {sys.version.split()[0]})"
    )
    
    # Check required modules
    print("\n[2] Checking Python Modules...")
    required_modules = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'sqlalchemy',
        'psycopg2',
        'pandas',
        'openpyxl',
        'werkzeug'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            all_checks_passed &= print_status(f"Module: {module}", True)
        except ImportError:
            all_checks_passed &= print_status(f"Module: {module}", False, "(Not installed)")
    
    # Check project structure
    print("\n[3] Checking Project Structure...")
    required_files = [
        'app/__init__.py',
        'app/models.py',
        'app/routes/auth.py',
        'app/routes/dashboard.py',
        'app/routes/data_entry.py',
        'app/templates/base.html',
        'config.py',
        'init_db.py',
        'run.py',
        'requirements.txt'
    ]
    
    for file_path in required_files:
        status = os.path.exists(file_path)
        all_checks_passed &= print_status(f"File: {file_path}", status)
    
    # Check required directories
    print("\n[4] Checking Directories...")
    required_dirs = [
        'app/templates',
        'app/routes',
        'app/services'
    ]
    
    for dir_path in required_dirs:
        status = os.path.isdir(dir_path)
        all_checks_passed &= print_status(f"Directory: {dir_path}", status)
    
    # Try to import Flask app
    print("\n[5] Checking Flask Application...")
    try:
        from app import create_app
        app = create_app()
        all_checks_passed &= print_status("Flask App Creation", True)
        
        # Check routes registered
        routes_count = len(list(app.url_map.iter_rules()))
        all_checks_passed &= print_status(
            "Routes Registered",
            routes_count > 10,
            f"({routes_count} routes)"
        )
    except Exception as e:
        all_checks_passed &= print_status("Flask App Creation", False, f"({str(e)})")
    
    # Check database connection (if configured)
    print("\n[6] Checking Database Configuration...")
    try:
        from config import Config
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        all_checks_passed &= print_status(
            "Database URI Configured",
            'postgresql://' in db_uri.lower(),
            "(PostgreSQL)"
        )
    except Exception as e:
        all_checks_passed &= print_status("Database Configuration", False, f"({str(e)})")
    
    # Summary
    print_header("Verification Summary")
    
    if all_checks_passed:
        print("\n✓ All checks passed!")
        print("\nNext steps:")
        print("  1. Configure your PostgreSQL database (see INSTALL.md)")
        print("  2. Update config.py with database credentials")
        print("  3. Run: python init_db.py")
        print("  4. Run: python run.py")
        print("  5. Open: http://localhost:5000")
        print("  6. Login: admin / admin123")
    else:
        print("\n✗ Some checks failed!")
        print("\nPlease fix the issues above and run this script again.")
        print("See INSTALL.md for detailed installation instructions.")
    
    print("\n" + "=" * 70 + "\n")
    
    return 0 if all_checks_passed else 1

if __name__ == '__main__':
    sys.exit(main())
