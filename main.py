"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.azure import make_azure_blueprint, azure
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError 
from parser import Parser
from image_link import Image_Count_Manager
from login import LoginForm, User, SMTP_User, Google_User, Azure_User
import os

app = Flask(__name__)
app.secret_key = ""

google_bp = make_google_blueprint(
    client_id="",
    client_secret="",
    scope=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/gmail.send"],
    redirect_to="login_google"
)
app.register_blueprint(google_bp, url_prefix="/login")

azure_bp = make_azure_blueprint(
    client_id="",
    client_secret="",
    scope=["https://graph.microsoft.com/Mail.Send", "https://graph.microsoft.com/Mail.ReadWrite"],
    redirect_to="login_azure"
)
app.register_blueprint(azure_bp, url_prefix="/login")

sessions = {"google": google, "azure": azure}

login_manager = LoginManager()
login_manager.init_app(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Allow running on localhost without https
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1" # Server may give more scopes than requested 

wsgi_app = app.wsgi_app

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

image_count_manager = Image_Count_Manager()

pseudo_database = {}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    # To load from database here.
    # Note: This function will be ran with every user interaction by flask_login to ensure security.
    return User.load(user_id, pseudo_database, sessions)

@app.route('/logout', methods=['GET'])
#@login_required # Allowed since "Logout" button is still in login page
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = SMTP_User(form.email.data, form.password.data)
        pseudo_database[user.get_id()] = ("SMTP", form.email.data, form.password.data)
        login_user(user, remember=True)
        next = request.args.get('next')
        # !TO VALIDATE IN PRODUCTION APP!
        # if not url_has_allowed_host_and_scheme(next, request.host):
        #     return flask.abort(400)
        return redirect(next or url_for('index'))
    return render_template('login.html', form=form)

@app.route('/login_google', methods=['GET'])
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))
    try:
        email = google.get("/oauth2/v1/userinfo").json()["email"]
    except (InvalidGrantError, TokenExpiredError):
        return redirect(url_for("google.login"))
    
    user = Google_User(email, google)
    pseudo_database[user.get_id()] = ("Google", email)
    login_user(user, remember=True)
    return redirect(url_for('index'))

@app.route('/login_azure', methods=['GET'])
def login_azure():
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    try:
        email = azure.get("/v1.0/me").json()["userPrincipalName"]
    except (InvalidGrantError, TokenExpiredError):
        return redirect(url_for("azure.login"))
    
    user = Azure_User(email, azure)
    pseudo_database[user.get_id()] = ("Azure", email)
    login_user(user, remember=True)
    return redirect(url_for('index'))

#goes to the upload.html website
#csv_file and body_file comes from index.html website
@app.route('/upload', methods=['POST'])
def upload_file():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if 'csv_file' not in request.files or 'body_file' not in request.files:
        flash('Missing file(s)')
        return redirect(url_for('index'))
    csv_file = request.files['csv_file']
    body_file = request.files['body_file']
    if csv_file.filename == '' or body_file.filename == '':
        flash('No selected file(s)')
        return redirect(url_for('index'))
    if csv_file and body_file:
        #get file paths for both and put them in the uploads folder
        csv_name = csv_file.filename
        csvpath = os.path.join(app.config['UPLOAD_FOLDER'], csv_name)
        csv_file.save(csvpath)

        body_name = body_file.filename
        bodypath = os.path.join(app.config['UPLOAD_FOLDER'], body_name)
        body_file.save(bodypath)

        #using the parser class to prepare the emails
        parser = Parser(csvpath, bodypath)
        department_input = request.form.get('department_search')
        emails_dept = parser.prepare_all_emails(attach_transparent_images=False)

        departments = []
        for email in emails_dept:
            departments.append(email['department'])
        departments.sort()
        departments = set(departments)
        if department_input not in departments:
            flash(f'There is no user in the given department: "{department_input}"')
            return redirect(url_for('index'))

        department = department_input if department_input else "all"

        try:
            parser = Parser(csvpath, bodypath)
            if "view-counts" in request.form:
                emails = parser.prepare_all_emails(department, attach_transparent_images=False)
            else:
                emails = parser.prepare_all_emails(department)
                for email in emails:
                    recipient = email['email']
                    subject = email['subject']
                    body = email['body']
                    current_user.send_message(recipient, subject, body)
            
            parser.update_report_data(emails)
            report = parser.prepare_report()
            hashes = [email['hash'] for email in emails]
            image_count_manager.update_unique_id_list(hashes)

            return render_template('upload.html', emails=emails, report=report)
        except Exception as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('index'))

@app.get("/update_count")
def update_count():
    return image_count_manager.get_image_counts()

#if needed
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    """
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
    """
    app.run(debug=True)
