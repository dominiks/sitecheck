'''
Configuration and methods for sending mails.
'''
import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "localhost"

replyto = "noreply@example.com"
server = None

def connectToServer():
    """ Establish a connection to the specified smtp server. """
    global server
    if server is not None:
        closeConnection()

    server = smtplib.SMTP()
    server.connect(SMTP_SERVER)

def closeConnection():
    """ Close the connection to the server. """
    global server
    if server is not None:
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
    global replyto

    if server is None:
        connectToServer()

    to = safe_unicode(to)
    subject = safe_unicode(subject)
    text = safe_unicode(text)

    msg = MIMEText(text.encode("UTF-8"), "plain", "UTF-8")
    msg["Subject"] = subject
    msg["To"] = to
    msg["Reply-to"] = replyto

    server.sendmail(msg["Reply-to"], msg["To"], msg.as_string())

def safe_unicode(textstring):
    """ Returns a unicode representation of the given string. """
    try:
        return unicode(textstring, "UTF-8")
    except TypeError:
        return textstring #was already unicode
