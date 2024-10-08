from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Google email
    username = db.Column(db.String(100), nullable=False)  # Name from Google
    password_hash = db.Column(db.String(255), nullable=True)  # Not used, but required for compatibility
    phone_number = db.Column(db.String(25), nullable=True)
    role = db.Column(db.Integer, nullable=True)  # 1 for student, 2 for counselor, 3 for director
    is_approved = db.Column(db.Boolean, default=False)  # Indicates if the user is approved by a director


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    details = db.Column(db.Text)
    submission_time = db.Column(db.DateTime, default=db.func.now())
    decision_time = db.Column(db.DateTime)
    decision_message = db.Column(db.Text)
    counselor_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class AbsenceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    what_was_missed = db.Column(db.String(20), nullable=False)
    time_missed = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    submission_time = db.Column(db.DateTime, default=db.func.now().op('AT TIME ZONE')('Asia/Jerusalem'))
    decision_time = db.Column(db.DateTime)
    counselor_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class ShabbatSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    submission_time = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    student = db.relationship('User', backref='shabbat_submissions', lazy=True)
