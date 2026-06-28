import imaplib
import email
import smtplib
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# কনফিগারেশন
EMAIL = "sgdev@netc.fr"
PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

def send_reply(to_email, original_subject):
    try:
        msg = email.message.EmailMessage()
        msg.set_content("okay bro I can see it shortly (it is a automation by Shubhomoy)")
        msg['Subject'] = f"Re: {original_subject}"
        msg['From'] = EMAIL
        msg['To'] = to_email

        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"Reply sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.get("/run")
def check_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # সব মেইল চেক করার জন্য 'ALL' ব্যবহার করছি যাতে কনফার্ম হওয়া যায়
        _, messages = mail.search(None, 'UNSEEN')
        
        if not messages[0]:
            print("No new messages found!")
            mail.logout()
            return {"status": "No new messages"}

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = email.message_from_bytes(msg_data[0][1])
            subject = raw_email['Subject']
            sender = raw_email.get("From")
            
            body = ""
            if raw_email.is_multipart():
                for part in raw_email.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
            else:
                body = raw_email.get_payload(decode=True).decode()

            print(f"Received from {sender}: {body[:50]}")

            if any(x in body.lower() for x in ["hi", "hello", "please try my web"]):
                send_reply(sender, subject)
                mail.store(num, '+FLAGS', '\\Seen')
        
        mail.logout()
        return {"status": "Checked and processed"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "Error", "detail": str(e)}

@app.get("/")
def home():
    return {"status": "Automation is active!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
