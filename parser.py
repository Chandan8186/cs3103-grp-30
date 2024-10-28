from image_link import make_image_links
import pandas as pd
import asyncio
import hashlib

class Parser:
    """
    Parser class to parse, prepare and track mail data.

    Attributes:
    sender (str): Sender's email ID.
    mail_data_path (str): Path to mail data CSV file.
    mail_body_path (str): Path to mail body txt file.

    Mail data csv headers: email, name, department

    Mail body text file format: subject, followed by empty line, followed by body

    Sample usage:
    parser = Parser('myself@gmail.com', 'data.csv', 'body.txt')
    emails = parser.prepare_all_emails_MIMEMultipart('department-A5')
    # send emails
    parser.update_report_data(emails)
    report = parser.prepare_report()
    print(report)
    """
    def __init__(self, sender, mail_data_path, mail_body_path):
        self.sender = sender
        self.mail_data_path = mail_data_path
        self.mail_body_path = mail_body_path
        self.report = {}

    def _read_mail_data(self):
        """
        Reads mail data CSV file.

        Returns: pd.df: DataFrame containing emails, names and departments.
        """
        df = pd.read_csv(self.mail_data_path, dtype=str)
        required_fields = ['email', 'name', 'department']
        if not all(col in df.columns for col in required_fields):
            raise ValueError(f"{self.mail_data_path} must contain 'email', 'name', and 'department' columns")
        if df.isna().any().any():
            raise ValueError(f"{self.mail_data_path} must not contain empty values")
        return df
    
    def _filter_by_department(self, mail_data_df, department='all'):
        """
        Filters mail_data df by given department.
        
        Parameters:
        mail_data_df (pd.df): DataFrame containing emails, names and departments.
        department (str): Department code to filter by.

        Returns:
        pd.df: Filtered dataframe containing recipients from given department.
        """
        if department.lower() == 'all':
            return mail_data_df
        return mail_data_df[mail_data_df['department'] == department]

    def _read_mail_body(self):
        """
        Reads email body file.

        Returns:
        str, str: Subject, body of email template.
        """
        with open(self.mail_body_path, 'r') as file:
            file_content = file.read().split('\n\n', 1)
            if len(file_content) < 2:
                raise ValueError(f"{self.mail_body_path} must contain subject and body separated by empty line")
            return file_content[0], file_content[1]

    def _prepare_email_content(self, template_subject, template_body, recipient_data):
        """
        Prepares email subject and body for given recipient.
        
        Parameters:
        template_subject (str): Subject of email template.
        template_body (str): Body of email template.
        recipient_data (dict): Recipient data containing name, email and department.

        Returns:
        str, str: Subject and body of email template.
        """
        subject = template_subject
        subject = subject.replace('#name#', recipient_data['name'])
        subject = subject.replace('#department#', recipient_data['department'])

        body = template_body
        body = body.replace('#name#', recipient_data['name'])
        body = body.replace('#department#', recipient_data['department'])

        md5_hash = hashlib.md5((subject + body).encode()).hexdigest()
        return subject, body, md5_hash

    def _attach_transparent_images(self, emails):
        hashes = [email['hash'] for email in emails]
        image_links = asyncio.run(make_image_links(hashes))

        for i in range(len(emails)):
            emails[i]['body'] = emails[i]['body'].replace('</body>', f'<img src="{image_links[i]}"></body>', 1)

    def prepare_all_emails(self, department='all'):
        """
        Prepares email subject and body for all recipients in string format.
        
        Parameters:
        department (str): Department code to filter by.

        Returns:
        list of dicts, each dict with email, name, department, subject and body
        """
        # 1. Read email IDs, names and department codes
        try:
            mail_data_df = self._read_mail_data()
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None

        # 2. Filter by department code
        filtered_mail_data_df = self._filter_by_department(mail_data_df, department)
        emails = filtered_mail_data_df.to_dict(orient='records')

        # 3. Read template subject and body
        try:
            template_subject, template_body = self._read_mail_body()
        except Exception as e:
            print(f"Error reading template file: {e}")
            return None
    
        # 4. Prepare all emails
        for i in range(len(emails)):
            subject, body, md5_hash = self._prepare_email_content(template_subject, template_body, emails[i])
            emails[i]['subject'] = subject
            emails[i]['body'] = body
            emails[i]['hash'] = md5_hash
            emails[i]['id'] = str(i)
        
        # 5. Attach 1x1 transparent images
        self._attach_transparent_images(emails)

        return emails

    def update_report_data(self, emails):
        """
        Updates sent email counts in email report.
        
        Parameters:
        emails: list of dicts, each dict with email, name, department, subject and body
        """
        for person in emails:
            if person['department'] not in self.report:
                self.report[person['department']] = 1
            else:
                self.report[person['department']] += 1

    def prepare_report(self):
        """
        Prepares email report as printable string.

        Returns:
        str: Report.
        """
        header = "Number of emails sent by department codes:\n\n"
        counts = [f"{key}: {value}\n" for key, value in self.report.items()]
        counts.sort()
        return header + ''.join(counts)
