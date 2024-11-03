"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.azure import make_azure_blueprint, azure
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError 
from parser import Parser
from image_link import Image_Count_Manager
from login import LoginForm, User, SMTP_User, Google_User, Azure_User
import os
import keyring
import json

app = Flask(__name__)
app.secret_key = "testing"

# Please register an OAuth app at Google Cloud / Microsoft Azure to generate client_id and client_secret
# Additionally, please ensure that you have given the app the necessary API permissions such as scopes,
# redirect uri, permitted emails if testing, etc. Note that Azure does only allows localhost for http,
# and NOT 127.0.0.1.
google_bp = make_google_blueprint(
    client_id="",
    client_secret="",
    redirect_to="login_google",
    scope=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/gmail.send"]
)
azure_bp = make_azure_blueprint(
    client_id="",
    client_secret="",
    redirect_to="login_azure",
    scope=["https://graph.microsoft.com/User.Read", "https://graph.microsoft.com/Mail.Send"]
)

app.register_blueprint(google_bp, url_prefix="/login")
app.register_blueprint(azure_bp, url_prefix="/login") 

login_manager = LoginManager()
login_manager.init_app(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Allow running on localhost without https
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1" # Server may give more scopes than requested 

wsgi_app = app.wsgi_app

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

image_count_manager = Image_Count_Manager()

def store_secret(key_name, secret_value):
    keyring.set_password('SmartMailerApp', key_name, secret_value)
def retrieve_secret(key_name):
    return keyring.get_password('SmartMailerApp', key_name)
def delete_secret(key_name):
    keyring.delete_password('SmartMailerApp', key_name)

parser = None

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    # Note: This function will be ran with every page refresh by flask_login to ensure security.
    return User.load(user_id)

@app.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        delete_secret(user_id)
        logout_user()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data
        user = SMTP_User(email, password)
        user_data_json = json.dumps({'password': password})
        store_secret(user.get_id(), user_data_json)
        login_user(user, remember=True)

        next = request.args.get('next')
        # !TO VALIDATE IN PRODUCTION APP! (with a valid domain name)
        # if not url_has_allowed_host_and_scheme(next, request.host):
        #     return flask.abort(400)
        return redirect(next or url_for('index'))
    return render_template('login.html', form=form)

@app.route('/login_google', methods=['GET'])
def login_google():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if not google.authorized:
        return redirect(url_for("google.login"))
    try:
        email = google.get("/oauth2/v1/userinfo").json()["email"]
    except (InvalidGrantError, TokenExpiredError):
        return redirect(url_for("google.login"))
    
    user = Google_User(email)
    store_secret(user.get_id(), json.dumps({}))

    login_user(user, remember=True)
    return redirect(url_for('index'))

@app.route('/login_azure', methods=['GET'])
def login_azure():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    try:
        email = azure.get("/v1.0/me").json()["userPrincipalName"]
    except (InvalidGrantError, TokenExpiredError):
        return redirect(url_for("azure.login"))
    
    user = Azure_User(email)
    store_secret(user.get_id(), json.dumps({}))

    login_user(user, remember=True)
    return redirect(url_for('index'))


#goes to the preview.html website
#csv_file and body_file comes from index.html website
@app.route('/preview', methods=['POST'])
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
        try:
            # set the global parser variable
            global parser
            parser = Parser(csvpath, bodypath)
        except Exception as e:
            flash(f"{e}")
            return redirect(url_for('index'))

        department_input = request.form.get('department_search')
        if department_input and department_input != "all" and department_input not in parser.departments:
            flash(f'There is no user in the given department: "{department_input}"')
            return redirect(url_for('index'))

        department = department_input if department_input else "all"

        try:
            if "view-counts" in request.form:
                emails = parser.prepare_all_emails(department, attach_transparent_images=False)
                parser.update_report_data(emails)
                report = parser.prepare_report()
                hashes = [email['hash'] for email in emails]
                image_count_manager.update_unique_id_list(hashes)
                return render_template('upload.html', emails=emails, report=report)
            else:
                return render_template('preview.html', department=department, subject=parser.subject, body=parser.body)

        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            return redirect(url_for('index'))


# asks for user confirmation then sends the emails
@app.route('/upload', methods=['POST'])
def preview_and_send():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    try:
        if "go-back" in request.form:
            return redirect(url_for('index'))
        
        emails = parser.prepare_all_emails(request.form.get('department'))
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
        flash(f'An error occurred: {str(e)}')
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
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000
    app.run(HOST, PORT, debug=True)
    """
    #could use the above to make sure the uri is localhost
    app.run(debug=True)
