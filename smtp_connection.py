from parser import *

import smtplib
import sys


class SMTP_Connection:
    """
    SMTP_Connection class to encapsulate SMTP connection to mail server

    Attributes:
        host (str): Hostname of mail server
        port (int): Port number to inform server to establish SMTP connection using SSL or TLS
        user (str): Email address of user
        password (str): User's password or Application password generated by user

    Sample usage:
    smtp_server = SMTP_Connection('smtp.gmail.com', 587, '<Your Email Address>', '<App Password Generated>')
    smtp_server.connect()
    ...
    <prepare email>
    ... 
    # Send message
    smtp_server.send(<email crafted>)
    """
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.smtp = None
    
    def connect(self):
        """
        Establishes SMTP connection to given SMTP server.
        """
        self.smtp = smtplib.SMTP(self.host, self.port)
        self.smtp.starttls()
        try:
            self.smtp.login(self.user, self.password)
        except Exception as err:
            print(f'Unable to connect or login into {self.host} due to the following reason:')
            print(str(err))
            sys.exit(1)
    
    def __del__(self):
        """
        Disconnects SMTP connection with mail server
        """
        if self.smtp:
            self.smtp.quit()
    
    def send_message(self, msg):
        """
        Sends email to target recipient

        Parameter:
            msg (email.message.EmailMessage) : Email message containing the recipient, subject and body
        """
        try:
            self.smtp.send_message(msg)
        except Exception as err:
            print("Unable to send message to recipient due to the following reason:")
            print(str(err))
            sys.exit(2)