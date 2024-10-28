from parser import *
from O365 import Account, FileSystemTokenBackend
from O365 import Message as O365Message
from email.message import EmailMessage

import smtplib
import sys


class SMTP_Connection:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.smtp = None
    
    def connect(self):
        self.smtp = smtplib.SMTP(self.host, self.port)
        self.smtp.starttls()
        try:
            self.smtp.login(self.user, self.password)
        except smtplib.SMTPHeloError as HeloErr:
            print('Server did not like us :(')
            print(str(HeloErr))
            sys.exit(2)
        except smtplib.SMTPAuthenticationError as AuthErr:
            print("Invalid Username/Password! Sure or not ur password/username correct?")
            print(str(AuthErr))
            sys.exit(1)
        except smtplib.SMTPNotSupportedError as SMTPNotSupportedErr:
            print("Server has a major skill issue by not having SMTP >:(")
            print(str(SMTPNotSupportedErr))
            sys.exit(1)
        except smtplib.SMTPException as smtpErr:
            print("Your standard so high no wonder no authentication methods want you")
            print(str(smtpErr))
            sys.exit(1)
    
    def terminate(self):
        self.smtp.quit()
    

    def send_message(self, recipient, subject, body):
        msg = EmailMessage()
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body, subtype="html")
        try:
            self.smtp.send_message(msg, self.user)
        except smtplib.SMTPRecipientsRefused as RecipientErr:
            print("Bro you sending email to ghost ah?")
            print(str(RecipientErr))
            sys.exit(2)
        except smtplib.SMTPHeloError as HeloErr:
            print("Just now server like you now it doesn't what you do sia")
            print(str(HeloErr))
            sys.exit(2)
        except smtplib.SMTPSenderRefused as SenderRefusedErr:
            print("Wah you kena blacklisted by server ah?")
            print(str(SenderRefusedErr))
            sys.exit(2)
        except smtplib.SMTPDataError as dataErr:
            print("Something cock up")
            print(str(dataErr))
            sys.exit(2)
        except smtplib.SMTPNotSupportedError as SMTPNotSupportedErr:
            print("Server got some beef with SMTPUTF8")
            print(str(SMTPNotSupportedErr))
            sys.exit(1)

class OutlookEmailSender:
    def __init__(self, client_id, client_secret, token_path='.'):
        """
        Initialize OAuth authentication for Outlook
        
        Args:
            client_id (str): Azure App Registration client ID
            client_secret (str): Azure App Registration client secret
            token_path (str): Path to store OAuth tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Define OAuth scopes
        self.scopes = [
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/Mail.ReadWrite'
        ]
        
        # Set up token backend
        self.token_backend = FileSystemTokenBackend(
            token_path=token_path,
            token_filename='o365_token.txt'
        )
        
        # Initialize account
        self.account = Account(self.client_id,
                             token_backend=self.token_backend,
                             scopes=self.scopes,
                             auth_flow_type='public')

    def authenticate(self):
        """
        Perform OAuth authentication
        Returns:
            bool: True if authentication successful
        """
        if not self.account.is_authenticated:
            # This will open a web browser for authentication
            result = self.account.authenticate()
            print("Authentication successful!" if result else "Authentication failed!")
            return result
        return True

    def send_message(self, recipient, subject, body):
        """
        Send an email using OAuth authentication
        
        Args:
            to_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body content
            attachments (list): List of file paths to attach (optional)
            
        Returns:
            bool: True if email sent successfully
        """

        try:
            if not self.authenticate():
                print("Authentication failed!")
                return False
            

            # Create message
            message = self.account.new_message()
            message.to.add(recipient)
            message.subject = subject
            message.body = body

            # Send the message
            result = message.send()
            print("Email sent successfully!" if result else "Failed to send email!")
            return result

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
