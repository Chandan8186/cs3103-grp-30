from flask_dance.contrib.azure import azure
from flask_dance.contrib.google import google
from wtforms import Form, StringField, PasswordField, validators, ValidationError
from email.message import EmailMessage
from base64 import urlsafe_b64encode
from smtp_connection import SMTP_Connection
from keyring import get_password
import keyring
import json

def retrieve_secret(key_name):
    return keyring.get_password('SmartMailerApp', key_name)

SMTP_SERVERS = {"yahoo.com": "smtp.mail.yahoo.com", 
                "gmail.com": "smtp.gmail.com", 
                "hotmail.com": "smtp-mail.outlook.com", 
                "outlook.com": "smtp-mail.outlook.com"}

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
        self.password = None
        self.access_token = None
        self.oauth = None
        self.email_sender = None
        self.oauth_type = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

    def get_id(self):
        return f"{self.email}_{self.oauth_type == None}"

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
    """
    Sets up user as a logged in outlook account.
    This function should only be called AFTER it has been authorized
    """
    def login_outlook(self, email, token):
        self.oauth = "outlook"
        self.email = email
        self.is_authenticated = azure.authorized
        self.is_active = self.is_authenticated
        self.access_token = token
        return f"{self.email}_{self.oauth_type == None}"
    
    def _get_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["From"] = self.email
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")
        return msg
    
    @staticmethod
    def load(user_id, sessions):
        # Retrieve user data from keyring
        data = retrieve_secret(user_id)
        if not data:
            return None

        # Parse the JSON data
        try:
            user_info = json.loads(data)
        except json.JSONDecodeError:
            return None
        user_type = user_info.get('user_type')
        email = user_info.get('email')

        if user_type == 'SMTP':
            password = user_info.get('password')
            return SMTP_User(email, password)
        elif user_type == 'Google':
            return Google_User(email, sessions["google"])
        elif user_type == 'Azure':
            return Azure_User(email, sessions["azure"])
        else:
            return None


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
        create_headers = {"Authorization": f'Bearer {self.access_token}',
                   "Content-Type": "application/json"}
        # Tried to emulate what was done for _send_google but creating the message that way created an error
        create_message = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address":recipient
                    }
                }
            ]
        }

        create_rsp = azure.post("https://graph.microsoft.com/v1.0/me/messages", headers=create_headers, json=create_message)

        message_id = ""
        if (create_rsp.ok):
            message_id = create_rsp.json()["id"]

            send_headers = {"Authorization": f'Bearer {self.access_token}'}
            # In Outlook REST API, {id} refers to the id of the message you want to send 
            # hence why a seperate request to craft a message was made
            send_rsp = azure.post(f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/send", headers=send_headers)
            if (not send_rsp.ok):
                print("Failed to send message")
            print(send_rsp)
        else :
            print("Failed to create message")
 