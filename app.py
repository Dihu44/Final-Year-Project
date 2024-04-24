from flask import Flask,render_template,request, jsonify, flash, url_for, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
import sqlite3
from datetime import datetime, timedelta
from forms import RegistrationForm, LoginForm, QueryForm
from ir_system import IRSystem

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(150), unique = True)
    password_hash = db.Column(db.String(150))
    joined_at = db.Column(db.DateTime(), default = datetime.utcnow)
    num_of_logins = db.Column(db.Integer, default = 0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

@app.route('/')
def home():
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log out the user
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()	
    if request.method == 'POST' and form.validate_on_submit():
        try:
            user = User(username=form.username.data, first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data)
            user.set_password(form.password1.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created!', 'success')

            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists. Please use a different email.', 'error')

    return render_template('register.html', form=form)

def iterate_files(folder_path):
    paths = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            #print("Processing:", item_path)
            paths.append(item_path)
        elif os.path.isdir(item_path):
            return paths + iterate_files(item_path)
    return paths

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    form = QueryForm()
    query_result = (0,0)
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data
        url = form.url.data
        print(query)
        out_directory = "/home/dihutswane/Documents/School/Final-Year-Project/downloads"

        """
        command = f"wget -m -p -E -k -np --directory-prefix={out_directory} {url}"
        result_of_download = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result_of_download.returncode == 0:
            print("Download completed successfully.")
        else:
            print("Error downloading file:")
            print(result_of_download.stderr)
        """

        paths = iterate_files(out_directory)
        result = IRSystem()
        html_paths = [path for path in paths if path.endswith('.html')]
        print(html_paths)
        result.index_collection(html_paths)
    
        result.query(query)
        for i in result.present_results(query):
        	print(i)
        query_result = (query, result)
        #return render_template('result2.html', query_result=query_result)

    return render_template('dashboard.html', form=form, query_result=query_result)

#Used to create the table defined in the User class/model
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)