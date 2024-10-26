from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from parser import Parser
from smtp_connection import SMTP_Connection

import time

def send_Email_To_Eng_Dept_Test():
    user = "muhammadarshadshaik@yahoo.com.sg"
    password = "tamtricxchlnoeub"
    department = "Eng"
    smtp_test = SMTP_Connection("smtp.mail.yahoo.com", 587, user, password)
    parser_test = Parser(user, "test/parser_test.csv", "test/parser_test.txt")

    smtp_test.connect()

    print("Connection Established")

    emails_to_send = parser_test.prepare_all_emails(department)

    for email in emails_to_send:
        recipient = email["email"]
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = recipient
        msg['Subject'] = email['subject']

        msg.attach(MIMEText(email['body'], 'html'))

        smtp_test.send_message(recipient, msg.as_string())

        print(f"message send to {recipient}")

        time.sleep(1)

send_Email_To_Eng_Dept_Test()