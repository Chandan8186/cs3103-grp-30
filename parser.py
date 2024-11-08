from image_link import make_image_links
import pandas as pd
import asyncio
import hashlib
import re

# Email regex is roughly based on RFC 5322 and 1034 of Internet Message Format
# it may not allow for some (likely rare) addresses
# Source: https://www.w3.org/TR/2012/WD-html-markup-20120329/input.email.html
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$')

class Parser:
    """
    Parser class to parse, prepare and track mail data.

    Attributes:
    mail_data_path (str): Path to mail data CSV file.
    mail_body_path (str): Path to mail body txt file.
    report (dict): Dictionary storing number of emails sent to each department.
    mail_data_df (pd.df): Dataframe containing mail data.
    headers (list): All headers specified by user. Must be at most 5. Must include name and department.
    departments (set): Set of all unique departments.
    subject (str): Mail subject template.
    body (str): Mail body template.

    Mail data csv headers: email, name, department

    Mail body text file format: subject, followed by empty line, followed by body

    Sample usage:
    parser = Parser('data.csv', 'body.txt')
    emails = parser.prepare_all_emails('department-A5')
    # send emails
    parser.update_report_data(emails)
    report = parser.prepare_report()
    print(report)
    """
    def __init__(self, mail_data_path, mail_body_path):
        self.mail_data_path = mail_data_path
        self.mail_body_path = mail_body_path
        self.report = {}
        self.headers = []

        # 1. Read mail data
        try:
            mail_data_df = pd.read_csv(self.mail_data_path, dtype=str)
        except pd.errors.EmptyDataError:
            raise Exception(f"{self.mail_data_path.replace('uploads/', '')} must not be empty.")
        except pd.errors.ParserError as e:
            raise Exception(f"Parsing error: {e}. Please fix {self.mail_data_path.replace('uploads/', '')} acordingly.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while reading mail data csv file: {e}")
        
        # 1.1. Check for required columns
        required_fields = ['email', 'name', 'department']
        if not all(col in mail_data_df.columns for col in required_fields):
            raise ValueError("Mail Data CSV must be a csv file containing at least 'email', 'name', and 'department' columns")
        if mail_data_df.isna().any().any():
            raise ValueError("Mail Data CSV must not contain empty values")

        self.mail_data_df = mail_data_df.drop_duplicates()

        # 1.2 Check for optional fields
        headers = self.mail_data_df.columns.tolist()
        if len(headers) - 3 > 3:
            raise ValueError("There should be at most 5 email fields (i.e. placeholders) including 'name' and 'department' in Mail Data CSV")
        with open(mail_data_path, 'r') as file:
            headers_temp = file.readline().strip().split(",")
        if len(headers_temp) != len(set(headers_temp)):
            raise ValueError("All email fields should be unique in Mail Data CSV")
        headers.remove('email')
        self.headers = headers

        # 1.3. Collate all departments
        departments = []
        for department in self.mail_data_df['department']:
            departments.append(department)
        departments.sort()
        self.departments = set(departments)

        if "all" in self.departments:
            raise ValueError("Mail Data CSV must not contain a department code named 'all'")

        # 1.4. Check for email address validity
        for email in self.mail_data_df['email']:
            if re.match(EMAIL_REGEX, email) is None:
                raise ValueError(f"At least one email address: '{email}' does not follow the RFC 5322 and 1034 format")

        # 2. Read mail body
        try:
            with open(self.mail_body_path, 'r') as file:
                file_content = file.read().split('\n\n', 1)
                if len(file_content) < 2:
                    raise ValueError(f"{self.mail_body_path.replace('uploads/', '')} must contain subject and body separated by empty line")
                if not file_content[1]:
                    raise ValueError("Email body must not be empty.")
                
        except Exception as e:
            raise Exception(f"An unexpected error occurred while reading mail body txt file: {e}")

        self.subject = file_content[0]
        self.body = file_content[1]
    
    def _filter_by_department(self, department='all'):
        """
        Filters mail_data df by given department.
        
        Parameters:
        mail_data_df (pd.df): DataFrame containing emails, names and departments (and optional headers).
        department (str): Department code to filter by.

        Returns:
        pd.df: Filtered dataframe containing recipients from given department.
        """
        if department.lower() == 'all':
            return self.mail_data_df
        return self.mail_data_df[self.mail_data_df['department'] == department]

    def _prepare_email_content(self, recipient_data):
        """
        Prepares email subject and body for given recipient.
        
        Parameters:
        template_subject (str): Subject of email template.
        template_body (str): Body of email template.
        recipient_data (dict): Recipient data containing name, email and department (and optional headers).

        Returns:
        str, str: Subject and body of email template.
        """
        subject = self.subject
        body = self.body

        for header in self.headers:
            subject = subject.replace('#' + header + '#', recipient_data[header])
            body = body.replace('#' + header + '#', recipient_data[header])

        md5_hash = hashlib.md5((recipient_data['email'] + subject + body).encode()).hexdigest()
        return subject, body, md5_hash

    def _attach_transparent_images(self, emails):
        hashes = [email['hash'] for email in emails]
        image_links = asyncio.run(make_image_links(hashes))

        for i in range(len(emails)):
            emails[i]['body'] = emails[i]['body'].replace('</body>', f'<img src="{image_links[i]}"></body>', 1)

    def prepare_first_email(self, department='all'):
        """
        Prepares email subject and body for all recipients in string format.
        This is used only for the preview page.

        Parameters:
        department (str): Department code to filter by.

        Returns:
        dict with email, name, department, subject and body
        """
        # 1. Filter by department code
        filtered_mail_data_df = self._filter_by_department(department)
        email = filtered_mail_data_df.to_dict(orient='records')[0]

        # 2. Prepare email
        subject, body, md5_hash = self._prepare_email_content(email)
        email['subject'] = subject
        email['body'] = body
        email['body_view'] = body
        email['hash'] = md5_hash
        email['id'] = str(0)

        return email

    def prepare_all_emails(self, department='all', attach_transparent_images=True):
        """
        Prepares email subject and body for all recipients in string format.
        
        Parameters:
        department (str): Department code to filter by.

        Returns:
        list of dicts, each dict with email, name, department, subject and body
        """
        # 1. Filter by department code
        filtered_mail_data_df = self._filter_by_department(department)
        emails = filtered_mail_data_df.to_dict(orient='records')

        # 2. Prepare all emails
        for i in range(len(emails)):
            subject, body, md5_hash = self._prepare_email_content(emails[i])
            emails[i]['subject'] = subject
            emails[i]['body'] = body
            emails[i]['body_view'] = body
            emails[i]['hash'] = md5_hash
            emails[i]['id'] = str(i)
        
        # 3. Attach 1x1 transparent images
        if attach_transparent_images:
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
