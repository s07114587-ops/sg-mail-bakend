import imaplib
import email
from email.message import EmailMessage
import smtplib
import os

# এনভায়রনমেন্ট ভেরিয়েবল থেকে পাসওয়ার্ড রিড করা
EMAIL = "sgdev@netc.fr"
PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

def send_reply(to_email, original_subject):
    msg = EmailMessage()
    msg.set_content("okay bro I can see it shortly (it is a automation by Shubhomoy)")
    msg['Subject'] = f"Re: {original_subject}"
    msg['From'] = EMAIL
    msg['To'] = to_email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)

def check_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    _, messages = mail.search(None, 'UNSEEN')
    for num in messages[0].split():
        _, msg_data = mail.fetch(num, '(RFC822)')
        raw_email = email.message_from_bytes(msg_data[0][1])
        subject = raw_email['Subject']
        sender = raw_email['From']
        
        # মেসেজ বডি চেক করা
        body = ""
        if raw_email.is_multipart():
            for part in raw_email.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = raw_email.get_payload(decode=True).decode()

        # কন্ডিশন চেক
        if "hi" in body.lower() or "how are you" in body.lower() or "please try my web" in body.lower():
            send_reply(sender, subject)
            mail.store(num, '+FLAGS', '\\Seen')

    mail.logout()

check_emails()
