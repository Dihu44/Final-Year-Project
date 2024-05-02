from flask import Flask,render_template,request, jsonify, flash, url_for, redirect, make_response, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
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

# Model for Users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(150), unique = True)
    password_hash = db.Column(db.String(150))
    joined_at = db.Column(db.DateTime(), default = datetime.utcnow)
    #num_of_logins = db.Column(db.Integer, default = 0)
    queries = db.relationship("Query", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

# Models for Queries
class Query(db.Model):
    query_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    query_text = db.Column(db.String(255))
    query_scoring_function = db.Column(db.String(10))
    query_stopwords = db.Column(db.String(255))
    k = db.Column(db.Float(), default = 0.0)
    b = db.Column(db.Float(), default = 0.0)
    query_timestamp = db.Column(db.DateTime(), default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    results = db.relationship("QueryResult", backref="query", lazy=True)

# Model for Query Results
class QueryResult(db.Model):
    result_id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.query_id'))
    document_title = db.Column(db.String(255))
    document_url = db.Column(db.String(255))
    document_score = db.Column(db.Float)

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
            username = user.username
            user_id = user.id
            return redirect(url_for('dashboard', user_id=user_id, username=username))

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
    user_id = request.args.get('user_id', '')
    username = request.args.get('username', '')

    form = QueryForm()
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data
        url = form.url.data
        scoring_function = form.scoring_function.data
        stopwords = form.stopwords.data
        stopwords_list = stopwords.split(',')
        stopwords = ' '.join(stopwords_list)

        return redirect(url_for('parameters', query=query, url=url, scoring_function=scoring_function, stopwords=stopwords, user_id=user_id, username=username))

    return render_template('dashboard.html', form=form, user_id=user_id, username=username)

@app.route('/parameters', methods=['GET', 'POST'])
@login_required
def parameters():
    user_id = request.args.get('user_id', '')
    username = request.args.get('username', '')
    query = request.args.get('query', '')
    url = request.args.get('url', '')
    scoring_function = request.args.get('scoring_function', '')
    stopwords = request.args.get('stopwords', '')

    form = ParameterForm()
    if request.method == 'POST' and form.validate_on_submit():

        k = form.k.data
        b = form.b.data
        number_of_docs = form.number_of_docs.data

        return redirect(url_for('results', query=query, url=url, scoring_function=scoring_function, stopwords=stopwords, k=k, b=b, number_of_docs=number_of_docs, user_id=user_id, username=username))

    return render_template('parameters.html', form=form, user_id=user_id, username=username)

@app.route('/results', methods=['GET', 'POST'])
@login_required
def results():
    user_id = request.args.get('user_id', '')
    username = request.args.get('username', '')
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

    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc

    folder_path = os.path.join(out_directory, domain_name)
    print(folder_path)

    if not os.path.isdir(folder_path):
        command = f"wget -m -p -E -k -np --directory-prefix={out_directory} {url}"
        result_of_download = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result_of_download.returncode == 0:
            #flash("Download completed successfully", "success")
            print("Success")
        else:
            #flash("Error downloading file: " + result_of_download.stderr, "error")
            #print(result_of_download.stderr)
            print("Error")
    
    paths = iterate_files(out_directory)
    if len(stopwords) > 0:
        result = IRSystem(stopwords)
    else:
        result = IRSystem()

    html_paths = [path for path in paths if path.endswith('.html')]

    result.index_collection(html_paths)
    results = []
    if k_float > 0.0 and b_float > 0.0 and number_of_docs_int > 0:
        results = result.present_results(query, number_of_docs_int, k_float, b_float)
    elif k_float > 0.0 and not (b_float > 0.0) and not (number_of_docs_int > 0):
        results = result.present_results(query, k=k_float)
    elif not (k_float > 0.0) and b_float > 0.0 and not (number_of_docs_int > 0):
        results = result.present_results(query, b=b_float)
    elif k_float > 0.0 and b_float > 0.0 and not (number_of_docs_int > 0):
        results = result.present_results(query, k=k_float, b=b_float)
    elif not (k_float > 0.0) and not (b_float > 0.0) and number_of_docs_int > 0:
        results = result.present_results(query, n=number_of_docs_int)
    elif k_float > 0.0 and not (b_float > 0.0) and number_of_docs_int > 0:
        results = result.present_results(query, n=number_of_docs_int, k=k_float)
    elif not (k_float > 0.0) and b_float > 0.0 and number_of_docs_int > 0:
        results = result.present_results(query, n=number_of_docs_int, b=b_float)
    else:
        results = result.present_results(query)

    query_record = Query(query_text = query, url = url, query_scoring_function = scoring_function, query_stopwords = stopwords, k = k_float, b = b_float, user_id = current_user.id)
    db.session.add(query_record)
    db.session.commit()

    for i in results:
        title = i.split('|')[2]
        url = '/'.join(i.split('|')[1].split('/')[1:])
        score = i.split('|')[0]
        query_result_record = QueryResult(query_id =query_record.query_id, document_title = title, document_url = url, document_score = score)
        db.session.add(query_result_record)

    db.session.commit()

    return render_template('results.html', scoring_function=scoring_function, results=results, query=query, username=username)

@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    queries = Query.query.filter_by(user_id=current_user.id).order_by(Query.query_timestamp.desc()).all()

    return render_template('history.html', queries=queries)

@app.route('/view_query_results', methods=['GET', 'POST'])
@login_required
def view_query_results():
    query_id = request.args.get('query_id', '')
    query_obj = Query.query.filter_by(query_id=query_id).first()
    query_text = query_obj.query_text
    url = query_obj.url
    scoring_function = query_obj.query_scoring_function
    results = query_obj.results

    return render_template('view_query_results.html', results=results, query=query_text, url=url, scoring_function=scoring_function)

#Used to create the table defined in the User class/model
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)