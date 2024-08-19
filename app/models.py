from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    details = db.Column(db.Text)
    submission_time = db.Column(db.DateTime, default=db.func.now())
    decision_time = db.Column(db.DateTime)
    counselor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
