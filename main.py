"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from parser import Parser
from smtp_connection import SMTP_Connection, OutlookEmailSender

import getpass
import os
import re

app = Flask(__name__)

wsgi_app = app.wsgi_app


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
        user = "myself@gmail.com"
        parser = Parser(user, csvpath, bodypath)
        emails = parser.prepare_all_emails('department-A5')
        try:
            parser = Parser(user, csvpath, bodypath)
            
            # ---------------------------------- How smtp_connection.py can be incorporated here ---------------------------------------
            # Prepare and send email to recipients
            # If email is a yahoomail or gmail, use SMTP_Connection class and prepare email contents in MIMEMUltipart
            # Else, use OutLookEmailSender class and prepare email contents in plain
            if (re.search(r".*@outlook.com", user)):
                email_sender = OutlookEmailSender("", "")
                
                if (not email_sender.authenticate()):
                    print("Unable to authenticate!") # Or perhaps a message back to GUI saying authentication issue
                    return redirect(url_for(index))

                emails = parser.prepare_all_emails('all')

                for email in emails:
                    recipient = email["email"]
                    subject = email['subject']
                    body = email['body']

                    email_sender.send_email(recipient, subject, body)

            else:
                email_sender = None
                password = getpass.getpass("Enter your app password: ") # Or we can try handling the password input on the frontend
                if (re.search(r".*@yahoo.com", user)): 
                    email_sender = SMTP_Connection("smtp.mail.yahoo.com", 587, user, password)
                elif (re.search(r".*@gmail.com", user)):
                    email_sender = SMTP_Connection("smtp.gmail.com", 587, user, password)
                else:
                    return redirect(url_for(index))
                
                emails = parser.prepare_all_emails_MIMEMultipart('all')

                for email in emails:
                    recipient = email['email']
                    msg = email['email_object']
                    email_sender.send_message(recipient, msg)
                
                
            parser.update_report_data(emails)
            report = parser.prepare_report()

            # ---------------------------------------------------------------------------------------------------------------------------
            #make a table to show the details
            #could add a count
            return render_template('upload.html', emails=emails, report=report)
        except Exception as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('index'))

        

        

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
