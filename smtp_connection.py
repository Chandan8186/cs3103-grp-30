import smtplib
import sys
from parser import *

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

#Test function to test the functionalities of SMTP_Connection
def main_test():
    user = ""
    password = ""

    test_msg = SMTP_Connection("smtp.office365.com", 587, user, password)
    test_msg.connect()

    print("Login successful!")

    test_msg.terminate()

if __name__ == "__main__":
    main_test()


        


