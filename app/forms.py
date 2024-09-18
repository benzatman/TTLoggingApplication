from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RequestForm(FlaskForm):
    request_type = SelectField('Request Type', choices=[
        ('checkin_extension', 'Check-in Extension'),
        ('overnight_absence', 'Overnight Absence'),
        ('general_absence', 'General Absence')
    ], validators=[DataRequired()])

    details = TextAreaField('Details', validators=[DataRequired()])

    submit = SubmitField('Submit Request')


class OffShabbatDestinationForm(FlaskForm):
    destination = StringField('Destination', validators=[DataRequired()])
    relation = StringField('Relation', validators=[DataRequired()])
    contact_info = TextAreaField('Contact Information', validators=[DataRequired()])

    submit = SubmitField('Submit Destination')


class AbsenceLoggingForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired()])
    what_was_missed = StringField('What Was Missed', validators=[DataRequired()])
    time_missed = StringField('Time Missed', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    details = TextAreaField('Additional Details')
    submit = SubmitField('Log Absence')

    reason = TextAreaField('Reason', validators=[DataRequired()])

    submit = SubmitField('Log Absence')
