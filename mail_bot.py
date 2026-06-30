import imaplib
import smtplib
import email
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
# CORS ইম্পোর্ট করা হলো
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

app = FastAPI(title="🔥 SGDEV Mail Automation 🔥")

# এই পার্টটাই সব প্ল্যাটফর্ম থেকে রিকোয়েস্ট এক্সেপ্ট করবে (Cross-Platform Fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # "*" মানে যেকোনো ওয়েবসাইট বা ক্রন-জব একে হিট করতে পারবে
    allow_credentials=True,
    allow_methods=["*"], # সব ধরণের রিকোয়েস্ট (GET, POST) এলাউড
    allow_headers=["*"],
)

# তোর মেইল কনফিগারেশন
EMAIL = "sgdev@netc.fr"
PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

# গলোবাল মেমোরি
latest_email_status = {
    "status": "Waiting for cron-job to check inbox...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A"
}

def send_reply(to_email, original_subject):
    try:
        msg = email.message.EmailMessage()
        msg.set_content("Hi! I received your mail. I will get back to you shortly. \n\nBest,\nShubhomoy (SGDEV)")
        safe_subject = original_subject if original_subject else "Your Mail"
        msg['Subject'] = f"Re: {safe_subject}"
        msg['From'] = EMAIL
        msg['To'] = to_email

        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"Reply sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending reply: {e}")

@app.get("/run")
def check_and_reply_inbox():
    global latest_email_status
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        _, messages = mail.search(None, 'UNSEEN')
        
        if not messages[0]:
            mail.logout()
            return {"status": "Success", "message": "Checked inbox. No new emails."}

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
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

            body = str(body) if body is not None else ""
            cleaned_body = body.replace('\r\n', '\n').strip()

            send_reply(sender, subject)
            mail.store(num, '+FLAGS', '\\Seen')

            latest_email_status = {
                "status": "🔥 New Mail Processed & Replied! 🔥",
                "sender": sender,
                "body": cleaned_body if cleaned_body else "(No text content found)",
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            }
        
        mail.logout()
        return {"status": "Success", "message": "Emails processed and replied!"}

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
                .meta {{ color: #8b949e; font-size: 0.9em; margin: 15px 0; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
                .highlight {{ color: #ff007f; font-weight: bold; font-size: 1.1em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Mail Automation Hub</h1>
                <p><strong>System Status:</strong> <span class="status-badge">{latest_email_status['status']}</span></p>
                <p class="meta"><strong>🕒 Last Updated:</strong> {latest_email_status['timestamp']}</p>
                <p><strong>📧 Last Sender:</strong> <span class="highlight">{latest_email_status['sender']}</span></p>
                <div style="text-align: left;">
                    <h3 style="color: #00ffcc;">📄 Received Message:</h3>
                    <div class="body-box">{latest_email_status['body']}</div>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
