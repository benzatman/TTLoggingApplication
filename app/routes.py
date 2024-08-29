from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from twilio.rest import Client
from datetime import datetime
from app import app, db
from app.models import User, Request
from app.forms import LoginForm, RequestForm, OffShabbatDestinationForm, AbsenceLoggingForm
from app.models import User


twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])


def get_phone_numbers_by_role(role):
    """Get the list of phone numbers for users with the specified role."""
    users = User.query.filter_by(role=role).all()
    return [f"whatsapp:{user.phone_number}" for user in users if user.phone_number]


def send_whatsapp_message_to_roles(roles, message):
    """Send a WhatsApp message to all users with the specified roles."""
    phone_numbers = []
    for role in roles:
        phone_numbers.extend(get_phone_numbers_by_role(role))

    for number in phone_numbers:
        twilio_client.messages.create(
            body=message,
            from_=app.config['TWILIO_WHATSAPP_FROM'],
            to=number
        )


def send_whatsapp_message(to_numbers, message):
    for number in to_numbers:
        twilio_client.messages.create(
            body=message,
            from_=app.config['TWILIO_WHATSAPP_FROM'],
            to=number
        )



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

        # Send WhatsApp message to directors and counselors
        message = f'You have a new request from {current_user.username}.'
        send_whatsapp_message_to_roles(['director', 'counselor'], message)

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


@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'director':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        role = request.form.get('role')
        password = request.form.get('password')

        if 'add_user' in request.form:
            new_user = User(
                username=username,
                password_hash=password,
                role=role,
                phone_number=phone_number
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully.', 'success')
        elif 'delete_user' in request.form:
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully.', 'success')

    return redirect(url_for('dashboard'))


@app.route('/statistics', methods=['GET', 'POST'])
@login_required
def statistics():
    if current_user.role != 'director':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    stats = {}
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            stats['total_requests'] = Request.query.filter_by(student_id=user.id).count()
            stats['approved_requests'] = Request.query.filter_by(student_id=user.id, status='approved').count()
            stats['rejected_requests'] = Request.query.filter_by(student_id=user.id, status='rejected').count()
            stats['absences'] = Request.query.filter_by(student_id=user.id, request_type='absence').count()

            # Calculate average response time
            response_times = []
            for req in Request.query.filter_by(counselor_id=user.id).all():
                if req.decision_time and req.submission_time:
                    response_times.append((req.decision_time - req.submission_time).total_seconds())
            if response_times:
                stats['avg_response_time'] = sum(response_times) / len(response_times)

        flash('Statistics calculated successfully.', 'success')

    return render_template('statistics.html', stats=stats)


@app.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    request = Request.query.get_or_404(request_id)
    if current_user.role not in ['counselor', 'director']:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('dashboard'))

    action = request.form.get('action')
    message = request.form.get('message')
    if action == 'approve':
        request.status = 'approved'
        request.decision_time = datetime.utcnow()
        request.decision_message = message
        request.counselor_id = current_user.id
        db.session.commit()

        # Notify the counselors and directors
        notification_message = f'Request from {request.student.username} was approved by {current_user.username}.'
        send_whatsapp_message_to_roles(['director', 'counselor'], notification_message)
        flash('Request approved.', 'success')
    elif action == 'reject':
        request.status = 'rejected'
        request.decision_time = datetime.utcnow()
        request.decision_message = message
        request.counselor_id = current_user.id
        db.session.commit()

        # Notify the counselors and directors
        notification_message = f'Request from {request.student.username} was rejected by {current_user.username}.'
        send_whatsapp_message_to_roles(['director', 'counselor'], notification_message)
        flash('Request rejected.', 'danger')

    return redirect(url_for('dashboard'))
