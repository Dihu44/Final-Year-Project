"""
This subsystem handles the creation of all the forms that will be used by the system.
It also handles input validation (Both frontend as well as backend thanks to the wftorms module.
Frontend validation is handled by injecting the python code directly to the html form pages.
"""

from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,SelectField,TextAreaField,DecimalField,IntegerField
from wtforms.validators import InputRequired,DataRequired,Email,EqualTo,URL,Regexp,Optional

# This is the form that will take data to facilitate the registration of users 
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators =[DataRequired(), InputRequired()])
    last_name = StringField('Last Name', validators =[DataRequired(), InputRequired()])
    username = StringField('Username', validators =[DataRequired(), InputRequired()])
    email = StringField('Email', validators=[DataRequired(),Email(), InputRequired()])
    password1 = PasswordField('Password', validators = [DataRequired(), InputRequired()])
    password2 = PasswordField('Confirm Password', validators = [DataRequired(), InputRequired(), EqualTo('password1')])
    submit = SubmitField('Register')

# This form will take data to facilitate the loggin in of users
class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# This form will take initial query data
class QueryForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), InputRequired(), URL(), Regexp(r'^https://www', message="URL must start with 'https://www'")])
    query = StringField('Query', validators=[DataRequired(), InputRequired()])
    stopwords = TextAreaField('Stopwords', validators=[Regexp(r"^[a-zA-Z]+(,[a-zA-Z]+)*$", message="Must contain comma separated words"), Optional()])
    scoring_function = SelectField('Scoring Function', choices=['BM25', 'Default'], validators=[DataRequired(), InputRequired()])
    submit = SubmitField('Submit')

# This form will take parameter data for the BM25 scoring function
class ParameterFormBM25(FlaskForm):
    k = DecimalField('k', validators=[Optional()])
    b = DecimalField('b', validators=[Optional()])
    number_of_docs = IntegerField('Number of Documents to be Returned', validators=[Optional()])
    submit = SubmitField('Submit')

# This form will take data for the default scoring function
class ParameterFormDefault(FlaskForm):
    number_of_docs = IntegerField('Number of Documents to be Returned', validators=[Optional()])
    submit = SubmitField('Submit')