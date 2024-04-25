from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,SelectField,TextAreaField,DecimalField
from wtforms.validators import InputRequired,DataRequired,Email,EqualTo,URL,Regexp,Optional

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators =[DataRequired(), InputRequired()])
    last_name = StringField('Last Name', validators =[DataRequired(), InputRequired()])
    username = StringField('Username', validators =[DataRequired(), InputRequired()])
    email = StringField('Email', validators=[DataRequired(),Email(), InputRequired()])
    password1 = PasswordField('Password', validators = [DataRequired(), InputRequired()])
    password2 = PasswordField('Confirm Password', validators = [DataRequired(), InputRequired(), EqualTo('password1')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class QueryForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), InputRequired(), URL()])
    query = StringField('Query', validators=[DataRequired(), InputRequired()])
    stopwords = TextAreaField('Stopwords', validators=[Regexp(r"^[a-zA-Z]+(,[a-zA-Z]+)*$", message="Must contain comma separated words"), Optional()])
    scoring_function = SelectField('Scoring Function', choices=['BM25'], validators=[DataRequired(), InputRequired()])
    submit = SubmitField('Submit')

class ParameterForm(FlaskForm):
    k = DecimalField('k', validators=[Optional()])
    b = DecimalField('b', validators=[Optional()])
    submit = SubmitField('Submit')