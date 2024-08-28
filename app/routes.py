from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db
from app.models import User, Request
from app.forms import LoginForm, RequestForm, OffShabbatDestinationForm, AbsenceLoggingForm


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        request_form = RequestForm()
        shabbat_form = OffShabbatDestinationForm()
        return render_template('student_dashboard.html', request_form=request_form, shabbat_form=shabbat_form)
    elif current_user.role == 'counselor':
        unanswered_requests = Request.query.filter_by(status='pending').all()
        absence_form = AbsenceLoggingForm()
        return render_template('counselor_dashboard.html', unanswered_requests=unanswered_requests, absence_form=absence_form)
    elif current_user.role == 'director':
        unanswered_requests = Request.query.filter_by(status='pending').all()
        absence_form = AbsenceLoggingForm()
        return render_template('director_dashboard.html', unanswered_requests=unanswered_requests, absence_form=absence_form)


@app.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
    form = RequestForm()
    if form.validate_on_submit():
        new_request = Request(
            student_id=current_user.id,
            request_type=form.request_type.data,
            details=form.details.data
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Request submitted successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/log_absence', methods=['POST'])
@login_required
def log_absence():
    form = AbsenceLoggingForm()
    if form.validate_on_submit():
        absence_record = Request(
            student_id=form.student_id.data,
            request_type='absence',
            details=form.reason.data,
            status='logged'
        )
        db.session.add(absence_record)
        db.session.commit()
        flash('Absence logged successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/manage_users', methods=['POST'])
@login_required
def manage_users():
    if current_user.role != 'director':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    if 'add_user' in request.form:
        # Add user logic
        pass
    elif 'delete_user' in request.form:
        # Delete user logic
        pass

    flash('User management action completed.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/statistics')
@login_required
def statistics():
    if current_user.role != 'director':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Logic to calculate statistics
    return render_template('statistics.html', stats=stats)
