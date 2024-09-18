from werkzeug.security import check_password_hash, generate_password_hash
from app.models import Request
from app.forms import LoginForm, RequestForm, OffShabbatDestinationForm, AbsenceLoggingForm
from twilio.rest import Client
from datetime import datetime
from flask import redirect, url_for, request, flash, render_template
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
from flask import current_app as app

twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])


# Set up OAuth
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])


# OAuth endpoints
def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()



def get_phone_numbers_by_role(role):
    """Get the list of phone numbers for users with the specified role."""
    users = User.query.filter_by(role=role).all()
    return [f"whatsapp:{user.phone_number}" for user in users if user.phone_number]


def send_whatsapp_message(to_numbers, message):
    """Send a WhatsApp message to a list of phone numbers."""
    for number in to_numbers:
        twilio_client.messages.create(
            body=message,
            from_=app.config['TWILIO_WHATSAPP_FROM'],
            to=number
        )


def send_whatsapp_message_to_roles(roles, message):
    """Send a WhatsApp message to all users with the specified roles."""
    phone_numbers = []
    for role in roles:
        phone_numbers.extend(get_phone_numbers_by_role(role))

    send_whatsapp_message(phone_numbers, message)


@app.route('/')
def home():
    return 'Hello, this is the home page! go to tlvbot.com/dashboard to see your dashboard.'


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 1:  # Student
        request_form = RequestForm()
        shabbat_form = OffShabbatDestinationForm()
        recent_requests = Request.query.filter_by(student_id=current_user.id).order_by(Request.submission_time.desc()).limit(5).all()
        return render_template('student_dashboard.html', request_form=request_form, shabbat_form=shabbat_form, recent_requests=recent_requests)
    elif current_user.role == 2:  # Counselor
        unanswered_requests = Request.query.filter_by(status='pending').all()
        absence_form = AbsenceLoggingForm()
        return render_template('counselor_dashboard.html', unanswered_requests=unanswered_requests, absence_form=absence_form)
    elif current_user.role == 3:  # Director
        unanswered_requests = Request.query.filter_by(status='pending').all()
        absence_form = AbsenceLoggingForm()
        unapproved_users = User.query.filter_by(is_approved=False).all()
        return render_template('director_dashboard.html', unanswered_requests=unanswered_requests, absence_form=absence_form, unapproved_users=unapproved_users)


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
        send_whatsapp_message_to_roles([2, 3], message)

        flash('Request submitted successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    request = Request.query.get_or_404(request_id)
    if current_user.role not in [2, 3]:
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

        # Notify the student
        student_phone = f"whatsapp:{request.student.phone_number}"
        notification_message = f'Your request was approved by {current_user.username}. Message: {message}'
        send_whatsapp_message([student_phone], notification_message)

        # Notify the counselors and directors
        notification_message = f'Request from {request.student.username} was approved by {current_user.username}.'
        send_whatsapp_message_to_roles([2, 3], notification_message)
        flash('Request approved.', 'success')
    elif action == 'reject':
        request.status = 'rejected'
        request.decision_time = datetime.utcnow()
        request.decision_message = message
        request.counselor_id = current_user.id
        db.session.commit()

        # Notify the student
        student_phone = f"whatsapp:{request.student.phone_number}"
        notification_message = f'Your request was rejected by {current_user.username}. Message: {message}'
        send_whatsapp_message([student_phone], notification_message)

        # Notify the counselors and directors
        notification_message = f'Request from {request.student.username} was rejected by {current_user.username}.'
        send_whatsapp_message_to_roles([2, 3], notification_message)
        flash('Request rejected.', 'danger')

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


@app.route('/statistics', methods=['GET', 'POST'])
@login_required
def statistics():
    if current_user.role != 3:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    stats = {}
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            stats['username'] = user.username
            stats['total_requests'] = Request.query.filter_by(student_id=user.id).count()
            stats['approved_requests'] = Request.query.filter_by(student_id=user.id, status='approved').count()
            stats['rejected_requests'] = Request.query.filter_by(student_id=user.id, status='rejected').count()
            stats['absences'] = Request.query.filter_by(student_id=user.id, request_type='absence').count()

            # Calculate average response time
            response_times = []
            for req in Request.query.filter_by(student_id=user.id).all():
                if req.decision_time and req.submission_time:
                    response_times.append((req.decision_time - req.submission_time).total_seconds())
            if response_times:
                stats['avg_response_time'] = sum(response_times) / len(response_times)

            flash('Statistics calculated successfully.', 'success')

    return render_template('statistics.html', stats=stats)


@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 3:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        role = int(request.form.get('role'))

        if 'add_user' in request.form:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(request.form.get('password')),
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


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('callback', _external=True),
        scope=['openid', 'email', 'profile'],
    )
    return redirect(request_uri)

@app.route('/callback')
def callback():
    code = request.args.get('code')

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg['token_endpoint']

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    email = userinfo['email']
    name = userinfo['name']

    # Check if user exists
    user = User.query.filter_by(email=email).first()

    if user:
        if user.is_approved:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('awaiting_approval.html')
    else:
        # Create a new user and mark as unapproved
        new_user = User(
            email=email,
            username=name,
            is_approved=False
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Your account is awaiting approval from a director.', 'info')
        return render_template('awaiting_approval.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/approve_users', methods=['GET', 'POST'])
@login_required
def approve_users():
    if current_user.role != 3:  # Only directors can approve users
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        phone_number = request.form.get('phone_number')
        role = int(request.form.get('role'))

        user = User.query.get(user_id)
        if user:
            user.phone_number = phone_number
            user.role = role
            user.is_approved = True
            db.session.commit()

            flash('User approved successfully.', 'success')
            return redirect(url_for('approve_users'))

    unapproved_users = User.query.filter_by(is_approved=False).all()
    return render_template('approve_users.html', unapproved_users=unapproved_users)
