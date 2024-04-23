from flask import Flask,render_template,request, jsonify, flash, url_for, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import sqlite3
import uuid
import jwt
import random
import base64
from forms import RegistrationForm, LoginForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique = True)
    username = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(150), unique = True)
    password_hash = db.Column(db.String(150))
    joined_at = db.Column(db.DateTime(), default = datetime.utcnow)
    num_of_logins = db.Column(db.Integer, default = 0)
    #token = db.Column(db.String(150), nullable = True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

@app.route('/')
def home():
    return render_template('index.html')

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.cookies:
            #token = request.headers['x-access-token']
            token = request.cookies['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401

        print(app.config['SECRET_KEY'])
        decoded_token = jwt.decode(token, base64.b64decode(app.config['SECRET_KEY']), algorithms=["HS256"])
        print(decoded_token)
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query\
                .filter_by(public_id = data['public_id'])\
                .first()
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated

# User Database Route
# this route sends back list of users (For testing purposes)
@app.route('/user', methods =['GET'])
@token_required
def get_all_users(current_user):
    # querying the database
    # for all the entries in it
    users = User.query.all()
    # converting the query objects
    # to list of jsons
    output = []
    for user in users:
        # appending the user data json
        # to the response list
        output.append({
            'public_id': user.public_id,
            'username': user.username,
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'email' : user.email
        })
  
    return jsonify({'users': output})

# route for logging user in
@app.route('/login', methods =['GET','POST'])
def login():

    if 'x-access-token' in request.cookies:
        token = request.cookies['x-access-token']
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            return jsonify({'message': 'User is already logged in cant perform another login'}), 200
        except jwt.DecodeError:
            print('decodeerrr')
            return jsonify({'message': 'Token is missing'}), 401

        except jwt.exceptions.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
    else:
        pass

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        
        if user is not None and user.check_password(form.password.data):
            #if user.num_of_login % 3 == 0:
                #resp = 
            token = jwt.encode({
            'public_id': user.public_id,
            'username': user.username,
            'uses': 3}, app.config['SECRET_KEY'])
            user.num_of_logins += 1
            db.session.commit()
            #session['logged_in'] = True
            #resp = make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
            resp = make_response(render_template('index.html'))
            #resp.set_cookie('x-access-token', token, expires= datetime.utcnow() + timedelta(minutes=20))
            #resp.set_cookie('x-access-token', token.decode('UTF-8'), expires= datetime.utcnow() + timedelta(minutes=20))
            request.session['X-access-token'] = token.decode('UTF-8'), expires= datetime.utcnow() + timedelta(minutes=2)
            #return redirect(url_for('index'))
            return resp
        else:
            return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
        )
    return render_template('login.html', form=form)

# signup route
@app.route('/register', methods =['GET', 'POST'])
def register():
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(public_id = str(uuid.uuid4()), username = form.username.data, first_name = form.first_name.data, last_name = form.last_name.data, email = form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/logout")
@token_required
def logout(current_user):

    #token = request.cookies['x-access-token']
    #data = jwt.decode(token, app.config['SECRET_KEY'])
    #if data['public_id']
    resp = make_response(render_template('index.html'))
    resp.set_cookie('x-access-token', expires = 0)
    return resp

#Used to create the table defined in the User class/model
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()