from wtforms import Form, StringField, PasswordField, validators, ValidationError
from email.message import EmailMessage
from base64 import urlsafe_b64encode
from smtp_connection import SMTP_Connection

SMTP_SERVERS = {"yahoo.com": "smtp.mail.yahoo.com", "gmail.com": "smtp.gmail.com"}

def validate_email(form, field):
    idx = field.data.rfind("@")
    email_server = field.data[idx + 1:]
    if idx == -1 or email_server not in SMTP_SERVERS:
        raise ValidationError("This field requires a valid email.")

class LoginForm(Form):
    email = StringField('Email Address', [validators.InputRequired("Please enter your email."), validate_email])
    password = PasswordField('Password', [validators.InputRequired("Please enter your password.")])

class User:
    def __init__(self):
        self.email = None
        self.oauth_type = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

    def get_id(self):
        return f"{self.email}_{self.oauth_type == None}"
    
    def _get_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["From"] = self.email
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")
        return msg
    
    @staticmethod
    def load(user_id, database, sessions):
        if user_id not in database:
            return None
        
        details = database[user_id]
        if details[0] == "SMTP":
            return SMTP_User(details[1], details[2])
        elif details[0] == "Google":
            return Google_User(details[1], sessions["google"])
        elif details[0] == "Outlook":
            return Outlook_User(details[1], sessions["outlook"])


class SMTP_User(User):
    def __init__(self, email, password):
        super().__init__()
        email_server = email[email.rfind("@") + 1:]
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
    def __init__(self, email, session):
        super().__init__()
        self.session = session
        self.oauth_type = "google"
        self.email = email
        self.is_authenticated = session.authorized
        self.is_active = self.is_authenticated

    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = urlsafe_b64encode(msg.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        rsp = self.session.post(f"/gmail/v1/users/{self.email}/messages/send", json=create_message)
        if not rsp.ok or "labelIds" not in rsp.json() or "SENT" not in rsp.json()["labelIds"]:
            print("Failed to send.")

"""
Encapsulates a signed in Azure account using OAuth.
This function should only be called AFTER it has been authorized.
"""
class Azure_User(User):
    def __init__(self, email, session):
        super().__init__()
        self.session = session
        self.oauth_type = "azure"
        self.email = email
        self.is_authenticated = session.authorized
        self.is_active = self.is_authenticated
    
    def send_message(self, recipient, subject, body):
        msg = self._get_message(recipient, subject, body)
        encoded_message = urlsafe_b64encode(msg.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        rsp = self.session.post(f"/gmail/v1/users/{self.email}/messages/send", json=create_message)
        if not rsp.ok or "labelIds" not in rsp.json() or "SENT" not in rsp.json()["labelIds"]:
            print("Failed to send.")
 