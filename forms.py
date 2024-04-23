from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Email,EqualTo, URL

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators =[DataRequired()])
    last_name = StringField('Last Name', validators =[DataRequired()])
    username = StringField('Username', validators =[DataRequired()])
    email = StringField('Email', validators=[DataRequired(),Email()])
    password1 = PasswordField('Password', validators = [DataRequired()])
    password2 = PasswordField('Confirm Password', validators = [DataRequired(),EqualTo('password1')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class QueryForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URL()])
    query = StringField('Query', validators=[DataRequired()])