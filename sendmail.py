'''
Configuration and methods for sending mails.
'''
import smtplib
from email.MIMEText import MIMEText

reply-to = "sender@example.com"
server = None

def connectToServer():
    """ Establish a connection to the specified smtp server. """
    global server
    server = smtplib.SMTP()
    server.connect("localhost")

def closeConnection():
    """ Close the connection to the server. """
    global server
    if server is None:
        server.close()

def sendmail(to, subject, text):
    """
    Send an email.

    When the connection to the server has not already been opened this method
    will attempt to do so.

    to      -- the email address to send the mail to
    subject -- the subject line to use
    text    -- the text to send
    """
    global server
    global reply-to

    if server is None:
        connectToServer()

    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["To"] = to
    msg["Reply-to"] = reply-to
    
    server.sendmail(msg["Reply-to"], msg["To"], msg.as_string())
