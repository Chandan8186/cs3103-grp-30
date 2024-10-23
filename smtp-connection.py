import getpass
import smtplib
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class SMTP_Connection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.smtp = None
    
    def connect(self, sender_user, sender_pass):
        self.smtp = smtplib.SMTP(self.host, self.port)
        self.smtp.starttls()
        try:
            self.smtp.login(sender_user, sender_pass)
        except smtplib.SMTPHeloError:
            print('Server did not like us :(')
        except smtplib.SMTPAuthenticationError as e:
            print("Invalid Username/Password! Sure or not ur password/username correct?")
            print(str(e))
            sys.exit(1)
        except smtplib.SMTPNotSupportedError:
            print("Server has a major skill issue by not having SMTP >:(")
        except smtplib.SMTPException:
            print("Your standard so high no wonder no authentication methods want you")
    
    def terminate(self):
        self.smtp.quit()
    

    def send_message(self, msg, sender, recipient):
        try:
            self.smtp.sendmail(sender, recipient, msg)
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




#Test function to test the functionalities of SMTP_Connection
def main_test():
    user = ""
    password = ""

    test_msg = SMTP_Connection("smtp.office365.com", 587)
    test_msg.connect(user, password)

    placeholders = dict()

    placeholders['subject'] = "Test email"
    placeholders['name'] = "Arshad"
    placeholders['department_code'] = "SOC"

    receiver = ""

    test_msg.send_message(test_msg.craft_message(user, receiver, placeholders), user, receiver)
    print("Message Sent")

    test_msg.terminate()

if __name__ == "__main__":
    main_test()


        


