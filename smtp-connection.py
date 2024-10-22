import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER = "" # input email of sender here
PASSWORD = "" # for gmail, generate application password

class SMTP_Connection:
    def __init__(self, host='smtp.gmail.com', port ='587'):
        self.host = host
        self.port = port
        self.smtp = None
    
    def connect(self):
        self.smtp = smtplib.SMTP(self.host, self.port)
        self.smtp.starttls()
        try:
            self.smtp.login(SENDER, PASSWORD)
        except smtplib.SMTPHeloError:
            print('Server did not like us :(')
        except smtplib.SMTPAuthenticationError:
            print("Invalid Username/Password! Sure or not ur password/username correct?")
        except smtplib.SMTPNotSupportedError:
            print("Server has a major skill issue by not having SMTP >:(")
        except smtplib.SMTPException:
            print("Your standard so high no wonder no authentication methods want you")
    
    def terminate(self):
        self.smtp.quit()
    
    def craft_message(self, recipient, placeholders):
        message = MIMEMultipart()
        message['From'] = SENDER
        message['To'] = recipient
        message['Subject'] = placeholders['subject']

        body = f'''
        <h1>{placeholders['name']} {placeholders['department_code']}</h1>
        <img src = {placeholders['img']}>
        '''

        mimetext = MIMEText(body, 'html')
        message.attach(mimetext)

        return message.as_string()

    def send_message(self, msg, recipient):
        try:
            self.smtp.sendmail(SENDER, recipient, msg)
        except smtplib.SMTPRecipientsRefused:
            print("Bro you sending email to ghost ah?")
        except smtplib.SMTPHeloError:
            print("Just now server like you now it doesn't what you do sia")
        except smtplib.SMTPSenderRefused:
            print("Wah you kena blacklisted by server ah?")
        except smtplib.SMTPDataError:
            print("Something cock up")
        except smtplib.SMTPNotSupportedError:
            print("Server got some beef with SMTPUTF8")
        


