"""
Authentication routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import User, AuditLog

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists
        if not user:
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.is_locked():
            flash(f'Account is locked until {user.locked_until.strftime("%Y-%m-%d %H:%M")}', 'danger')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            flash('Account is disabled. Contact administrator.', 'danger')
            return render_template('auth/login.html')
        
        # Verify password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.session.commit()
                flash('Too many failed attempts. Account locked for 30 minutes.', 'danger')
            else:
                remaining = 5 - user.failed_login_attempts
                flash(f'Invalid password. {remaining} attempts remaining.', 'danger')
            
            db.session.commit()
            return render_template('auth/login.html')

        
        # Successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.locked_until = None
        db.session.commit()
        
        login_user(user, remember=remember)
        
        # Log successful login
        audit = AuditLog(
            user_id=user.user_id,
            action_type='LOGIN',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            status='SUCCESS'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Redirect to dashboard or requested page
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log logout
    audit = AuditLog(
        user_id=current_user.user_id,
        action_type='LOGOUT',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        status='SUCCESS'
    )
    db.session.add(audit)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()
        
        # Log password change
        audit = AuditLog(
            user_id=current_user.user_id,
            action_type='PASSWORD_CHANGE',
            status='SUCCESS'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/change_password.html')
