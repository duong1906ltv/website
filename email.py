from . import mail
from flask_mail import Message

def send_mail(to, subject, template):
    msg = Message(subject,recipients = [to], html = template)
    mail.send(msg)
