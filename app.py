from flask import Flask,render_template,request, jsonify, flash, url_for, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
import sqlite3
from datetime import datetime, timedelta
from forms import RegistrationForm, LoginForm, QueryForm, ParameterForm
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
            paths.append(item_path)
        elif os.path.isdir(item_path):
            paths.extend(iterate_files(item_path))  # Recursive call
    return paths

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = QueryForm()
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data
        url = form.url.data
        scoring_function = form.scoring_function.data
        stopwords = form.stopwords.data
        stopwords_list = stopwords.split(',')
        stopwords = ' '.join(stopwords_list)
        print(stopwords)

        # Where the website will be downloaded to
        #out_directory = os.path.dirname(__file__) + "/downloads"

        """
        command = f"wget -m -p -E -k -np --directory-prefix={out_directory} {url}"
        result_of_download = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result_of_download.returncode == 0:
            flash("Download completed successfully", "success")
        else:
            flash("Error downloading file: " + result_of_download.stderr, "error")
            #print(result_of_download.stderr)
        """

        """
        paths = iterate_files(out_directory)
        result = IRSystem()
        html_paths = [path for path in paths if path.endswith('.html')]
        prefix = os.path.dirname(__file__)

        result.index_collection(html_paths)
        result.query(query)
        for i in result.present_results(query):
        	print(i)
        """
        return redirect(url_for('parameters', query=query, url=url, scoring_function=scoring_function, stopwords=stopwords))

    return render_template('dashboard.html', form=form)

@app.route('/parameters', methods=['GET', 'POST'])
@login_required
def parameters():
    query = request.args.get('query', '')
    url = request.args.get('url', '')
    scoring_function = request.args.get('scoring_function', '')
    stopwords = request.args.get('stopwords', '')

    form = ParameterForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Where the website will be downloaded to
        out_directory = os.path.dirname(__file__) + "/downloads"

        k = form.k.data
        b = form.b.data
        number_of_docs = form.number_of_docs.data

        return redirect(url_for('results', query=query, url=url, scoring_function=scoring_function, stopwords=stopwords, k=k, b=b, number_of_docs=number_of_docs))

    return render_template('parameters.html', form=form)

@app.route('/results', methods=['GET', 'POST'])
@login_required
def results():
    query = request.args.get('query', '')
    url = request.args.get('url', '')
    scoring_function = request.args.get('scoring_function', '')
    stopwords = request.args.get('stopwords', '')
    k = request.args.get('k', '')
    b = request.args.get('b', '')
    number_of_docs = request.args.get('number_of_docs', '')

    k_float = 0.0
    b_float = 0.0
    number_of_docs_int = 0
    if k:
    	k_float = float(k)
    if b:
    	b_float = float(b)
    if number_of_docs:
    	number_of_docs_int = int(number_of_docs)


    # Where the website will be downloaded to
    out_directory = os.path.dirname(__file__) + "/static"
    
    paths = iterate_files(out_directory)
    if len(stopwords) > 0:
        result = IRSystem(stopwords)
    else:
        result = IRSystem()

    html_paths = [path for path in paths if path.endswith('.html')]
    print(paths)

    result.index_collection(html_paths)
    results = []
    if k_float > 0.0 and b_float > 0.0 and number_of_docs_int > 0:
        """
        print(1)
        for i in result.present_results(query, number_of_docs_int, k_float, b_float):
            print(i)
        """
        results = result.present_results(query, number_of_docs_int, k_float, b_float)
    elif k_float > 0.0 and not (b_float > 0.0) and not (number_of_docs_int > 0):
        """
        print(2)
        for i in result.present_results(query, k=k_float):
            print(i)
        """
        results = result.present_results(query, k=k_float)
    elif not (k_float > 0.0) and b_float > 0.0 and not (number_of_docs_int > 0):
        """
        print(3)
        for i in result.present_results(query, b=b_float):
            print(i)
        """
        results = result.present_results(query, b=b_float)
    elif k_float > 0.0 and b_float > 0.0 and not (number_of_docs_int > 0):
        """
        print(4)
        for i in result.present_results(query, k=k_float, b=b_float):
            print(i)
        """
        results = result.present_results(query, k=k_float, b=b_float)
    elif not (k_float > 0.0) and not (b_float > 0.0) and number_of_docs_int > 0:
        """
        print(5)
        for i in result.present_results(query, n=number_of_docs_int):
            print(i)
        """
        results = result.present_results(query, n=number_of_docs_int)
    elif k_float > 0.0 and not (b_float > 0.0) and number_of_docs_int > 0:
        """
        print(6)
        for i in result.present_results(query, n=number_of_docs_int, k=k_float):
            print(i)
        """
        results = result.present_results(query, n=number_of_docs_int, k=k_float)
    elif not (k_float > 0.0) and b_float > 0.0 and number_of_docs_int > 0:
        """
        print(7)
        for i in result.present_results(query, n=number_of_docs_int, b=b_float):
            print(i)
        """
        results = result.present_results(query, n=number_of_docs_int, b=b_float)
    else:
        """
        print(8)
        for i in result.present_results(query):
            print(i)
        """
        results = result.present_results(query)

    print(results)

    return render_template('results.html', query=query, url=url, scoring_function=scoring_function, results=results)

#Used to create the table defined in the User class/model
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)