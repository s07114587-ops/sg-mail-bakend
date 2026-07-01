import imaplib
import smtplib
import email
import os
import time
from datetime import datetime

EMAIL = "sgdev@netc.fr"
PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

def send_reply(to_email, original_subject):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
        to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

        msg['Subject'] = f"Re: {safe_subject}"
        msg['From'] = EMAIL
        msg['To'] = to_email
        
        body_text = "Hi! I received your mail via Mailo server on PythonAnywhere. \n\nBest,\nShubhomoy (SGDEV)"
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        print(f"[{datetime.now().strftime('%X')}] Sending reply to {to_email} via Port 465 SSL...")
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=15) as smtp:
            smtp.ehlo()
            smtp.login(EMAIL, PASSWORD)
            smtp.sendmail(EMAIL, to_email, msg.as_string())
        print("✅ Reply successfully sent!")
    except Exception as e:
        print(f"🚨 SMTP Replying Failed: {e}")

def check_and_reply_inbox():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # শুধুমাত্র নতুন না-পঠিত (UNSEEN) মেইল চেক করবে
        _, messages = mail.search(None, 'UNSEEN')
        
        if not messages[0]:
            print(f"[{datetime.now().strftime('%X')}] Inbox checked: No new unseen emails.")
            mail.logout()
            return

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = email.message_from_bytes(msg_data[0][1])
            subject = raw_email.get('Subject', 'No Subject')
            sender = raw_email.get("From", "Unknown Sender")
            
            print(f"🔥 New mail found from: {sender} | Subject: {subject}")
            
            # রিপ্লাই পাঠানো হচ্ছে
            send_reply(sender, subject)
            
            # মেইলটিকে পঠিত (Seen) মার্ক করে দেওয়া হচ্ছে
            mail.store(num, '+FLAGS', '\\Seen')
        
        mail.logout()
    except Exception as e:
        print(f"🚨 IMAP Error: {e}")

if __name__ == "__main__":
    print("🚀 SGDEV Mail Automation Bot Started on PythonAnywhere...")
    if not PASSWORD:
        print("❌ Error: MAILO_PASSWORD environment variable is missing!")
    
    # প্রতি ৬০ সেকেন্ড পর পর ইনবক্স চেক করার লুপ
    while True:
        check_and_reply_inbox()
        print("Sleeping for 60 seconds...")
        time.sleep(60)
