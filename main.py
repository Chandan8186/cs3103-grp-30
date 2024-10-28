"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from parser import Parser
from smtp_connection import SMTP_Connection, OutlookEmailSender
from image_link import Image_Count_Manager

import getpass
import os

app = Flask(__name__)

wsgi_app = app.wsgi_app

SMTP_SERVERS = {"outlook.com": None, "hotmail.com": None, "yahoo.com": "smtp.mail.yahoo.com", "gmail.com": "smtp.gmail.com"}

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

image_count_manager = Image_Count_Manager()

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def login():
    # To obtain from user using GUI
    user_email = "myself@gmail.com"
    client_id = ""
    client_secret = ""
    token_path = "."

    email_sender = None
    ampersand_idx = user_email.rfind("@")
    if ampersand_idx == -1:
        print("Not a valid email address!")
        return None, None

    email_client = user_email[ampersand_idx + 1:]

    if email_client not in SMTP_SERVERS:
        print("Your email client is currently unsupported!")
        return None, None

    if email_client == "hotmail.com" or email_client == "outlook.com":
        email_sender = OutlookEmailSender(client_id, client_secret, token_path)
        if (not email_sender.authenticate()):
            print("Unable to authenticate!") # Or perhaps a message back to GUI saying authentication issue
            return None, None

    else:
        smtp_url = SMTP_SERVERS[email_client]
        password = getpass.getpass("Enter your app password: ") # Or we can try handling the password input on the frontend
        email_sender = SMTP_Connection(smtp_url, 587, user_email, password)
        email_sender.connect()

    return user_email, email_sender

#goes to the upload.html website
#csv_file and body_file comes from index.html website
@app.route('/upload', methods=['POST'])
def upload_file():
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
        department = "all" # Can be "all"
        user, email_sender = login()
        if user == None:
            return redirect(url_for(index))

        try:
            parser = Parser(user, csvpath, bodypath)
            emails = parser.prepare_all_emails(department)
            for email in emails:
                recipient = email['email']
                subject = email['subject']
                body = email['body']
                email_sender.send_message(recipient, subject, body)
            
            parser.update_report_data(emails)
            report = parser.prepare_report()
            hashes = [email['hash'] for email in emails]
            image_count_manager.update_unique_id_list(hashes)

            return render_template('upload.html', emails=emails, report=report)
        except Exception as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for(index))

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
