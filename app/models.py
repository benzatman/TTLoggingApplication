from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Integer, nullable=False)  # 1 for student, 2 for counselor, 3 for director
    phone_number_country_code = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)


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


class OffShabbatDestinationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shabbat_date = db.Column(db.DateTime, default=db.func.now().op('AT TIME ZONE')('Asia/Jerusalem'))
    relation_to_host = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    submission_time = db.Column(db.DateTime, default=db.func.now().op('AT TIME ZONE')('Asia/Jerusalem'))
