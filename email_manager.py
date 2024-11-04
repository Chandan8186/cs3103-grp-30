from flask import flash
from threading import Thread, Event
import time

# Note: Need to update these values in upload.html as well
INTERVAL = 62   
EMAILS_PER_INTERVAL = 20

"""
Manages email scheduling.
Emails are sent at the specified rate limit per interval.
Stores details regarding email being sent.
"""
class Email_Manager:
    def __init__(self):
        self.user = None
        self.emails = []
        self.has_ran = False
        self._thread = None
        self._cancel = Event()
        self.results = [] # Free to view while sending emails.
        self.report = None
        self.headers = None

    """
    Send all specified emails.
    EMAILS_PER_INTERVAL number of emails are sent every INTERVAL seconds.

    This function should not be called by the user directly. Use .send_emails() instead.
    This function can only be ran a single time for every Email_Scheduler instance.
    """
    def _send_emails(self):
        email_sent_count = 0
        start_time = time.time()

        for email in self.emails:
            if (email_sent_count == EMAILS_PER_INTERVAL):
                time_spent = time.time() - start_time
                self._cancel.wait(INTERVAL - time_spent)
                email_sent_count = 0
                start_time = time.time()
            if self._cancel.is_set():
                break
            
            recipient = email['email']
            subject = email['subject']
            body = email['body']

            self.results.append(self.user.send_message(recipient, subject, body))
            email_sent_count += 1

    """
    Start sending emails at specified rate limit.
    Parameters:
        user (User): The user object that will send the emails.
        emails (list[dict]): The emails to be sent.
    """
    def send_emails(self, user, emails):
        if self.has_ran:
            if self._thread.is_alive():
                flash("Note: The current batch of emails are still being sent. It was not sent again.")
            else:
                flash("Note: The current batch of emails have already been sent. It was not sent again.")
            return
        
        self.user = user
        self.emails = emails
        self.has_ran = True
        self._cancel.clear()
        self.results.clear()
        self._thread = Thread(target=self._send_emails)
        self._thread.start()

    """
    Returns status of whether email scheduler is sending emails.
    """
    def is_sending(self):
        return self.has_ran and self._thread.is_alive()
    
    """
    Allow next batch of emails to be sent.
    This is disallowed if the current batch is still being sent.

    Returns:
    bool: Success status of this function.
    """
    def allow_next_batch(self):
        if self.is_sending():
            flash("Note: The current batch of emails are still being sent. Please wait until it has finished sending.")
            return False

        self.has_ran = False
        return True
    
    """
    Stop sending the current batch of emails.
    """
    def cancel(self):
        if not self.is_sending():
            flash("There are no emails currently being sent to cancel.")
            return
        flash("Successfully cancelled.")
        self._cancel.set()

    """
    Store headers and report for currently sending emails.
    Used to coordinate between currently sending emails their relevant details
    """
    def store_header_and_report(self, headers, report):
        self.headers = headers
        self.report = report
    
