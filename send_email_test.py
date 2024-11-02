from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from parser import Parser
from smtp_connection import SMTP_Connection, OutlookEmailSender

import smtplib
import sys

def send_Yahoo_Or_Gmail_Email_To_Eng_Dept_Test():
    user = "" #enter yahoomail or gmail account
    password = "" #Get app password
    department = "Eng"

    # Yahoo SMTP server: smtp.mail.yahoo.com; Port: 587
    # Gmail SMTP server: smtp.gmail.com; Port: 587
    smtp_test = SMTP_Connection("smtp.mail.yahoo.com", 587, user, password) 

    # Make test csv and txt files
    parser_test = Parser(user, "uploads/test.csv", "uploads/body.txt")

    smtp_test.connect()

    print("Connection Established")

    emails_to_send = parser_test.prepare_all_emails_MIMEMultipart(department)

    successful_emails_sent = 0
    expected_successful_emails_sent = len(emails_to_send)

    for email in emails_to_send:
        recipient = email["email"]
        msg = email["email_object"]
        print(recipient)
        try:
            smtp_test.send_message(recipient, msg.as_string())
        except smtplib.SMTPException:
            continue
        
        successful_emails_sent += 1
        print(f"message send to {recipient}")

    print(f"Result: {expected_successful_emails_sent == successful_emails_sent}")

#send_Yahoo_Or_Gmail_Email_To_Eng_Dept_Test()