import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

app = FastAPI(title="🔥 SGDEV Ultimate Mail Bot 🔥")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📧 ইনবক্স রিড হবে মেলো (Mailo) থেকে
MAILO_EMAIL = "sgdev@netc.fr"
MAILO_PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"

# 🚀 রিপ্লাই যাবে জিমেইল (Gmail) এর সেফ রুট দিয়ে
GMAIL_USER = "তোর_নিজের_জিমেইল_আইডি@gmail.com"  # <--- এখানে তোর জিমেইল আইডি বসাবি
GMAIL_APP_PASS = os.getenv('GMAIL_APP_PASSWORD') # <--- রেন্ডারে এই ভেরিয়েবলটা সেট করব
SMTP_SERVER = "smtp.gmail.com"

global_memory = {
    "status": "Waiting for /run...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A",
    "smtp_error": "No errors tracked yet."
}

def send_reply(to_email, original_subject):
    global global_memory
    try:
        msg = MIMEMultipart()
        safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
        to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

        msg['Subject'] = f"Re: {safe_subject}"
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        
        body_text = "Hi! I received your mail via Mailo system. This is an automated reply from SGDEV Server. \n\nBest,\nShubhomoy (SGDEV)"
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        print("Sending reply via Gmail Secure SMTP...")
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=15) as smtp:
            smtp.ehlo()
            smtp.login(GMAIL_USER, GMAIL_APP_PASS)
            smtp.sendmail(GMAIL_USER, to_email, msg.as_string())
            
        global_memory["smtp_error"] = "✅ Successfully sent via Gmail Secure SMTP!"
        return True
    except Exception as e:
        final_error = f"🚨 Gmail SMTP Failed: {e}"
        print(final_error)
        global_memory["smtp_error"] = final_error
        return False

@app.get("/run")
def check_and_reply_inbox():
    global global_memory
    try:
        # মেলো থেকে মেইল রিড করা হচ্ছে
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(MAILO_EMAIL, MAILO_PASSWORD)
        mail.select("inbox")

        _, messages = mail.search(None, 'ALL')
        
        if not messages[0]:
            mail.logout()
            return {"status": "Success", "message": "Inbox is empty."}

        mail_ids = messages[0].split()
        latest_mail_id = mail_ids[-1] 

        _, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
        raw_email = email.message_from_bytes(msg_data[0][1])
        subject = raw_email.get('Subject', 'No Subject')
        sender = raw_email.get("From", "Unknown Sender")
        
        body = ""
        if raw_email.is_multipart():
            for part in raw_email.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
        else:
            payload = raw_email.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')

        cleaned_body = str(body).replace('\r\n', '\n').strip()

        # জিমেইল দিয়ে সেফ রিপ্লাই পাঠানো
        send_reply(sender, subject)

        global_memory["status"] = "🔥 Script Processed 🔥"
        global_memory["sender"] = sender
        global_memory["body"] = cleaned_body if cleaned_body else "(No text content)"
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        mail.logout()
        return {"status": "Processed", "smtp_status": global_memory["smtp_error"]}

    except Exception as e:
        return {"status": "Error", "detail": str(e)}

@app.get("/", response_class=HTMLResponse)
async def view_dashboard():
    html_content = f"""
    <html>
        <head>
            <title>SGDEV Mail Automation</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0a12; color: #c9d1d9; padding: 40px; text-align: center; }}
                .container {{ max-width: 700px; margin: auto; background: rgba(20, 20, 35, 0.9); padding: 30px; border-radius: 12px; border: 2px solid #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }}
                h1 {{ color: #ff007f; text-shadow: 0 0 10px #ff007f; margin-top: 0; }}
                .status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 6px; background: #00ffcc; color: black; font-weight: bold; font-size: 1.1em; }}
                .error-box {{ background: #1b2a1b; border: 1px solid #00ffcc; padding: 15px; border-radius: 6px; color: #99ff99; margin: 15px 0; font-family: monospace; text-align: left; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; word-break: break-all; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Mail Hybrid Automation Hub</h1>
                <p><strong>System Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                
                <h3 style="color: #00ffcc; text-align: left;">🔄 SMTP Output Log:</h3>
                <div class="error-box">{global_memory['smtp_error']}</div>

                <p><strong>📧 Last Sender:</strong> <span style="color: #ff007f; font-weight: bold;">{global_memory['sender']}</span></p>
                <div style="text-align: left;">
                    <h3 style="color: #00ffcc;">📄 Received Message from Mailo:</h3>
                    <div class="body-box">{global_memory['body']}</div>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
