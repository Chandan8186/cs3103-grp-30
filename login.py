from flask_dance.contrib.azure import azure
from flask_dance.contrib.google import google
from wtforms import Form, StringField, PasswordField, validators, ValidationError
from wtforms.csrf.session import SessionCSRF
from email.message import EmailMessage
from base64 import urlsafe_b64encode, b64encode
from smtp_connection import SMTP_Connection
from datetime import timedelta
from flask import session, flash
from parser import EMAIL_REGEX
import keyring
import json
import re

SMTP_SERVERS = {"yahoo.com": "smtp.mail.yahoo.com", 
                "gmail.com": "smtp.gmail.com", 
                "hotmail.com": "smtp-mail.outlook.com", 
                "outlook.com": "smtp-mail.outlook.com"}

def retrieve_secret(key_name):
    return keyring.get_password('SmartMailerApp', key_name)

def validate_email(form, field):
    email = field.data
    if re.match(EMAIL_REGEX, email) is None:
        raise ValidationError(f"'{email}' is not a valid email.")
    email_server = email[email.rfind("@") + 1:]
    if email_server not in SMTP_SERVERS:
        raise ValidationError("This email server is not currently supported.")

class LoginForm(Form):
    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = b"testing123"
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session
        
    email = StringField('Email Address', [validators.InputRequired("Please enter your email."), validate_email])
    password = PasswordField('Password', [validators.InputRequired("Please enter your password.")])

class User:
    def __init__(self):
        self.email = None
        self.email_type = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

    def get_id(self):
        return f"{self.email}_{self.email_type}"
    
    def _get_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["From"] = self.email
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")
        return msg
    
    @staticmethod
    def load(user_id):
        # Retrieve user data from keyring
        data = retrieve_secret(user_id)
        if not data:
            return None

        # Parse the JSON data
        try:
            user_info = json.loads(data)
        except json.JSONDecodeError:
            return None
        split_idx = user_id.rindex("_")
        email_type = user_id[split_idx + 1:]
        email = user_id[:split_idx]
        if email_type == 'smtp':
            password = user_info.get('password')
            return SMTP_User(email, password)
        elif email_type == 'google':
            return Google_User(email)
        elif email_type == 'azure':
            return Azure_User(email, None)
        return None
from urllib import request

class SMTP_User(User):
    def __init__(self, email, password):
        super().__init__()
        email_server = email[email.rfind("@") + 1:]
        self.email_type = "smtp"
        self.email = email
        self.password = password
        self.email_sender = SMTP_Connection(SMTP_SERVERS[email_server], 587, email, password)
        self.is_authenticated = True
        self.is_active = True

    def send_message(self, recipient, subject, body):
        if not self.email_sender.smtp:
            self.email_sender.connect()
        self.email_sender.send_message(self._get_message(recipient, subject, body))

"""
Encapsulates a signed in Google account using OAuth.
This function should only be called AFTER it has been authorized.
"""
class Google_User(User):
    def __init__(self, email):
        super().__init__()
        self.email_type = "google"
        self.email = email
        self.is_authenticated = google.authorized
        self.is_active = self.is_authenticated

    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = urlsafe_b64encode(msg.as_bytes()).decode()
        json_message = {"raw": encoded_message}
        rsp = google.post(f"/gmail/v1/users/{self.email}/messages/send", json=json_message)
        if not rsp.ok or "labelIds" not in rsp.json() or "SENT" not in rsp.json()["labelIds"]:
            flash(f"Failed to send email to {recipient} due to :{rsp.reason}.")

"""
Encapsulates a signed in Azure account using OAuth.
This function should only be called AFTER it has been authorized.
"""
class Azure_User(User):
    def __init__(self, email, access_token):
        super().__init__()
        self.email_type = "azure"
        self.email = email
        self.is_authenticated = azure.authorized
        self.is_active = self.is_authenticated
        self.access_token = access_token
    
    """
    Crafts an email and sends that email to target recipient
    Parameters:
        recipient (str): receiver of email to be crafted
        subject (str): subject of email to be crafted
        body (str): body content of email to be crafted
    """
    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = b64encode(msg.as_bytes()).decode()
        headers = {"Authorization": f'Bearer {self.access_token}', "Content-Type": "text/plain"}
        rsp = azure.post("/v1.0/me/sendMail", data=encoded_message, headers=headers)
        if (not rsp.ok):
            flash(f"Failed to send email to {recipient} due to :{rsp.reason}.")

 