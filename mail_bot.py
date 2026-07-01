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

app = FastAPI(title="🔥 SGDEV Mail Automation 🔥")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = "sgdev@netc.fr"
PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

global_memory = {
    "status": "Waiting for /run...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A",
    "smtp_error": "No errors tracked yet."  # এখানে লাইভ এরর দেখাবে
}

def send_reply(to_email, original_subject):
    global global_memory
    # ট্রাই করার আগে এরর ক্লিন করে নিচ্ছি
    global_memory["smtp_error"] = "Attempting to send..."
    
    try:
        msg = MIMEMultipart()
        safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
        to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

        msg['Subject'] = f"Re: {safe_subject}"
        msg['From'] = EMAIL
        msg['To'] = to_email
        
        body_text = "Hi! I received your mail via Mailo server. I will get back to you shortly. \n\nBest,\nShubhomoy (SGDEV)"
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # ৪৬৫ পোর্ট ট্রাই
        print("Trying Port 465 SSL...")
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=15) as smtp:
            smtp.ehlo()
            smtp.login(EMAIL, PASSWORD)
            smtp.sendmail(EMAIL, to_email, msg.as_string())
        global_memory["smtp_error"] = "✅ Successfully sent via Port 465 SSL!"
        return True
    except Exception as e1:
        error_msg = f"Port 465 Failed: {e1}"
        print(error_msg)
        
        # ৪৬৫ ফেল করলে ৫৮৭ ট্রাই
        try:
            print("Trying Port 587 STARTTLS...")
            with smtplib.SMTP(SMTP_SERVER, 587, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(EMAIL, PASSWORD)
                smtp.sendmail(EMAIL, to_email, msg.as_string())
            global_memory["smtp_error"] = "✅ Successfully sent via Port 587 STARTTLS!"
            return True
        except Exception as e2:
            final_error = f"🚨 Both Ports Failed! Port 465: {e1} | Port 587: {e2}"
            print(final_error)
            global_memory["smtp_error"] = final_error
            return False

@app.get("/run")
def check_and_reply_inbox():
    global global_memory
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, PASSWORD)
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

        # রিপ্লাই পাঠানো ট্রিগার
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
                .error-box {{ background: #2a1b1b; border: 1px solid #ff4444; padding: 15px; border-radius: 6px; color: #ff9999; margin: 15px 0; font-family: monospace; text-align: left; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; word-break: break-all; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Mail Automation Hub</h1>
                <p><strong>System Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                
                <h3 style="color: #ff4444; text-align: left;">⚠️ SMTP / Output Log:</h3>
                <div class="error-box">{global_memory['smtp_error']}</div>

                <p><strong>📧 Last Sender:</strong> <span style="color: #ff007f; font-weight: bold;">{global_memory['sender']}</span></p>
                <div style="text-align: left;">
                    <h3 style="color: #00ffcc;">📄 Received Message:</h3>
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
