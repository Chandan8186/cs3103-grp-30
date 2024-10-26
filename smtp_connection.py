from parser import *
from O365 import Account, FileSystemTokenBackend
from O365 import Message as O365Message

import os
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
        except smtplib.SMTPHeloError:
            print('Server did not like us :(')
        except smtplib.SMTPAuthenticationError as e:
            print("Invalid Username/Password! Sure or not ur password/username correct?")
            print(str(e))
            sys.exit(1)
        except smtplib.SMTPNotSupportedError:
            print("Server has a major skill issue by not having SMTP >:(")
        except smtplib.SMTPException as smtpErr:
            print("Your standard so high no wonder no authentication methods want you")
            print(str(smtpErr))
            sys.exit(1)
    
    def terminate(self):
        self.smtp.quit()
    

    def send_message(self, recipients, msg_bodies):
        for i in range(len(recipients)):
            try:
                self.smtp.sendmail(self.user, recipients[i], msg_bodies[i])
            except smtplib.SMTPRecipientsRefused:
                print("Bro you sending email to ghost ah?")
            except smtplib.SMTPHeloError:
                print("Just now server like you now it doesn't what you do sia")
            except smtplib.SMTPSenderRefused:
                print("Wah you kena blacklisted by server ah?")
            except smtplib.SMTPDataError as dataErr:
                print("Something cock up")
                print(str(dataErr[1]))
                sys.exit(2)
            except smtplib.SMTPNotSupportedError:
                print("Server got some beef with SMTPUTF8")

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

    def send_email(self, to_email, subject, body, attachments=None):
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
            message.to.add(to_email)
            message.subject = subject
            message.body = body

            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        message.attachments.add(file_path)

            # Send the message
            result = message.send()
            print("Email sent successfully!" if result else "Failed to send email!")
            return result

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False


#Test function to test the functionalities of SMTP_Connection
def main_test():
    user = "" # If using outlook, provide client id
    password = "" # If using outlook, provide client secret

    test_outlook = OutlookEmailSender("", "")

    test_outlook.authenticate()

    test_outlook.send_email("", "", "", None)

    #test_msg = SMTP_Connection("smtp-mail.outlook.com", 587, user, password)
    #test_msg.connect()

    #print("Login successful!")

    #test_msg.terminate()

if __name__ == "__main__":
    main_test()


        


