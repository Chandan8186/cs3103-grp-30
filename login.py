from flask_dance.contrib.azure import azure
from flask_dance.contrib.google import google
from wtforms import Form, StringField, PasswordField, validators, ValidationError
from wtforms.csrf.session import SessionCSRF
from email.message import EmailMessage
from base64 import urlsafe_b64encode, b64encode
from smtp_connection import SMTP_Connection
from datetime import timedelta
from flask import session
from parser import EMAIL_REGEX
import keyring
import json
import re

SMTP_SERVERS = {"gmail.com": "smtp.gmail.com", 
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

"""
A form used to obtain SMTP email and password from the user.
"""
class LoginForm(Form):
    class Meta:
        csrf = True
        csrf_class = SessionCSRF # Uses session-based Cross-Site Request Forgery for secure transfer of details.
        csrf_secret = b"testing123"
        csrf_time_limit = timedelta(minutes=20) # Set to renew to ensure security

        @property
        def csrf_context(self):
            return session
        
    email = StringField('Email Address', [validators.InputRequired("Please enter your email."), validate_email])
    password = PasswordField('Password', [validators.InputRequired("Please enter your password.")])

"""
Encapsulates a user.
Used with Flask-Login to manage user details.
"""
class User:
    def __init__(self):
        self.email = None
        self.email_type = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

    """
    Returns a unique identifier for this user.
    """
    def get_id(self):
        return f"{self.email}_{self.email_type}"
    
    """
    Returns a MIME format representation of the email message.
    Parameters:
        recipient (str): receiver of email to be crafted.
        subject (str): subject of email to be crafted.
        body (str): body content of email to be crafted.
    """
    def _get_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["From"] = self.email
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")
        return msg
    
    """
    Loads the user with the matching user_id from keyring.
    Parameters:
        user_id (str): Unique identifier of the user.
    """
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
            return Azure_User(email)
        return None

"""
Encapsulates an SMTP user.
Verification of email and password is left to the SMTP server.
"""
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

    """
    Crafts an email and sends that email to target recipient.
    Parameters:
        recipient (str): receiver of email to be crafted.
        subject (str): subject of email to be crafted.
        body (str): body content of email to be crafted.
    Returns: (str): Error messages from sending email. Empty if successful.
    """
    def send_message(self, recipient, subject, body):
        if not self.email_sender.smtp:
            result = self.email_sender.connect()
            if result != "Success":
                return result
        return self.email_sender.send_message(self._get_message(recipient, subject, body))

"""
Encapsulates a signed in Google account using OAuth.
An object should be instantiated only be called AFTER it has been authorized.
"""
class Google_User(User):
    def __init__(self, email):
        super().__init__()
        self.email_type = "google"
        self.email = email
        self.session = google._get_current_object()
        self.is_authenticated = self.session.authorized
        self.is_active = self.is_authenticated

    """
    Crafts an email and sends that email to target recipient.
    Parameters:
        recipient (str): receiver of email to be crafted.
        subject (str): subject of email to be crafted.
        body (str): body content of email to be crafted.
    Returns: (str): Error messages from sending email. Empty if successful.
    """
    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = urlsafe_b64encode(msg.as_bytes()).decode()
        json_message = {"raw": encoded_message}
        rsp = self.session.post(f"/gmail/v1/users/{self.email}/messages/send", json=json_message)
        if not rsp.ok or "labelIds" not in rsp.json() or "SENT" not in rsp.json()["labelIds"]:
            return "Error: " + rsp.reason
        return "✓"

"""
Encapsulates a signed in Azure account using OAuth.
An object should be instantiated only be called AFTER it has been authorized.
"""
class Azure_User(User):
    def __init__(self, email):
        super().__init__()
        self.email_type = "azure"
        self.email = email
        self.session = azure._get_current_object()
        self.is_authenticated = self.session.authorized
        self.is_active = self.is_authenticated
    
    """
    Crafts an email and sends that email to target recipient
    Parameters:
        recipient (str): receiver of email to be crafted.
        subject (str): subject of email to be crafted.
        body (str): body content of email to be crafted.
    Returns: (str): Error messages from sending email. Empty if successful.
    """
    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = b64encode(msg.as_bytes()).decode()
        headers = {"Authorization": f'Bearer {self.session.access_token}', "Content-Type": "text/plain"}
        rsp = self.session.post("/v1.0/me/sendMail", data=encoded_message, headers=headers)
        if (not rsp.ok):
            return "Error: " + rsp.reason
        return "✓"

 