from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class FBForm(FlaskForm):
    gcp_proj = StringField('GCP Project ID:', validators=[DataRequired()])
    submit = SubmitField('Create')


class CreateAndroidAppForm(FlaskForm):
    fb_proj = StringField('FireBase Project ID:', validators=[DataRequired()])
    display_name = StringField('Display Name of App:', validators=[DataRequired()])
    name = StringField('Name of App:', validators=[DataRequired()])
    submit = SubmitField('Create')


class AndroidAppForm(FlaskForm):
    fb_proj = StringField('FB Project ID:', validators=[DataRequired()])
    submit = SubmitField('Get Apps')