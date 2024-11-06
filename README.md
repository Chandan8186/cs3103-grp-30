# cs3103-grp-30
This is a project for [Option 1] Smart Mailer Program for CS3103 Assignment. 

## Contents
* [Introduction](#introduction)
* [Setting up](#setting-up-smart-mailer-program)
* [Features](#features)
    *  [Logging in(OAuth)](#logging-into-your-account-oauth)
    *  [Logging in(password)](#logging-into-your-account-password)
    *  [Uploading files](#uploading-files)
    *  [Previewing Email](#preview-and-sending-emails)
    *  [Viewing counts](#viewing-counts)
    *  [Logging Out](#logging-out)
* [Troubleshooting](#troubleshooting)
    *  [Unable to login(OAuth)](#unable-to-login-via-oauth)
    *  [Unable to login(OAuth) second time](#unable-to-login-via-oauth-the-second-time)
    *  [Unable to send email for google Oauth](#unable-to-send-email-for-google-oauth)


## Introduction

This smart mailer program will send mails to a list of emails provided in a csv using outlook, gmail and other smtp services. The program reads the rows and columns of the csv and replace the variable names of the draft email provided and send out each customized emails to the users.

## Setting up Smart Mailer Program
After git cloning the program, pip install the modules in the requirements.txt:
```
git clone https://github.com/Chandan8186/cs3103-grp-30.git
#unzip and cd into the folder
pip install -r requirements.txt
```
Launch the program with the following command:
```
python main.py
```
If it is successful it should launch the web application on the localhost server:
```
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 120-854-820
127.0.0.1 - - [04/Nov/2024 18:13:00] "GET / HTTP/1.1" 302 -
127.0.0.1 - - [04/Nov/2024 18:13:00] "GET /login HTTP/1.1" 200 -
127.0.0.1 - - [04/Nov/2024 18:13:00] "GET /static/style.css HTTP/1.1" 200 -
127.0.0.1 - - [04/Nov/2024 18:13:01] "GET /favicon.ico HTTP/1.1" 404 -
```
Opening the web application should look something like this:
![main index](images/mainIndex.png)

**Note: if you are planning to use an Outlook Account to log in, please use this url: ```http://localhost:5000```**

## Features
The smart mailer program allows you to send multiple resources and track them with ease on your email session

### Logging into your account OAuth

Google and Outlook OAuth are available for the web application

To get the client id and client secret for the your account, follow the [Google](https://developers.google.com/identity/protocols/oauth2/web-server#python) and [Outlook](https://learn.microsoft.com/en-us/partner-center/marketplace-offers/create-or-update-client-ids-and-secrets) official documentation and for authorized urls do as follow:

```
#Outlook
http://localhost:5000/login/azure/authorized
#Google
http://127.0.0.1:5000/login/google/authorized
```

Here is an example:
![Credentials](images/credentialGoogle.png)

Enter the client ID and secret into the code at the follow area of main.py, you may need to launch the web application again:
![Code Main](images/codeMain.png)

### Logging into your account password

Enter the valid email and password for your email account. Do note that some email providers like Gmail and Yahoo Mail requires users to input an application password as the password instead of their actual password.

**Note: Outlook only supports OAuth Authentication. Please refer to the instructions for logging into your account using [OAuth](#logging-into-your-account-oauth).** 

### Uploading files

After successfully logging in, upload your mail data csv file and mail body text file, followed by the department code to send to.

We included a maildata.csv and body.txt test files for you to try and undertstand the formattings
![upload](images/upload.png)

### Preview and Sending Emails

Before sending the emails, you can click on "Preview before sending" to check how the email looks like and which placeholders were replaced.

Make sure that it is exactly as you want it to be before sending the email!
![preview](images/preview.png)

### Viewing counts

If the mail is sent successfully, the following information would be displayed on the screen, showing the send status and the view count:
![Sent Mail](images/sentMail.png)

When a user opens the mail, the inbuilt redirect link tracker would trigger:

![Opening email](images/openMail.png)

The view count would increase as follows:

![View Count](images/viewCount.png)

### Logging out

Press the logout button at the top right of the webpage to exit

## Troubleshooting

### Unable to login via Oauth

1. Double check the client ID and secret key fields and that you have saved the edits
2. Verify that you have specified the necessary permissions. 
    - For Outlook, ensure you have specified the following API permissions and ensured that these permissions have been granted consent as shown below:

    ![Microsoft Azure API Perms](images/Microsoft%20Azure%20API%20Perms.JPG)

    - For Google, ensure you have specified the follwing API permissions
   

### Unable to login via Oauth the second time

Try clearing browsing cache or use incognito mode

### Unable to send email for Google Oauth

Try enabling IMAP access for your email account -> settings -> advanced settings -> forwarding and POP/IMAP:

![enable IMAP](images/IMAP.png)

Alternatively, You could also try SMTP login for Google
