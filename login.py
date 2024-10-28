from flask_dance.contrib.google import google
from wtforms import Form, StringField, PasswordField, validators, ValidationError
from email.message import EmailMessage
from base64 import urlsafe_b64encode
from smtp_connection import SMTP_Connection

SMTP_SERVERS = {"yahoo.com": "smtp.mail.yahoo.com", "gmail.com": "smtp.gmail.com"}

def validate_email(form, field):
    email_server = field.data[field.data.rfind("@") + 1:]
    if email_server not in SMTP_SERVERS:
        raise ValidationError("This field requires a valid email.")

class LoginForm(Form):
    email = StringField('Email Address', [validators.InputRequired("Please enter your email."), validate_email])
    password = PasswordField('Password', [validators.InputRequired("Please enter your password.")])

class User:
    def __init__(self):
        self.email = None
        self.password = None
        self.oauth = None
        self.email_sender = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

    def get_id(self):
        return f"{self.email}_{self.oauth == None}"

    def login_smtp(self, email, password):
        email_server = email[email.rfind("@") + 1:]
        self.email = email
        self.password = password
        self.email_sender = SMTP_Connection(SMTP_SERVERS[email_server], 587, email, password)
        self.email_sender.connect()
        self.is_authenticated = True
        self.is_active = self.is_authenticated
        return True

    """
    Sets up user as a logged in google account.
    This function should only be called AFTER it has been authorized.
    """
    def login_google(self, email):
        self.oauth = "google"
        self.email = email
        self.is_authenticated = google.authorized
        self.is_active = self.is_authenticated
    
    def send_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["From"] = self.email
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")

        if self.oauth == "google":
            self._send_google(msg)
        elif self.oauth == "outlook":
            pass
        else:
            self.email_sender.send_message(msg)

    def _send_google(self, msg):
        encoded_message = urlsafe_b64encode(msg.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        rsp = google.post(f"/gmail/v1/users/{self.email}/messages/send", json=create_message)
        if not rsp.ok or "labelIds" not in rsp.json() or "SENT" not in rsp.json()["labelIds"]:
            print("Failed to send.")
 