import imaplib
import smtplib
import socket
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
    "smtp_error": "No errors tracked yet."
}

def send_reply(to_email, original_subject):
    global global_memory
    
    # ১০০০ IQ ট্রিক: সকেটের ডিফল্ট টাইমআউট ৭ সেকেন্ড করে দেওয়া হলো যাতে কোড ঝুলে না থাকে
    socket.setdefaulttimeout(7.0)
    
    msg = MIMEMultipart()
    safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
    to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

    msg['Subject'] = f"Re: {safe_subject}"
    msg['From'] = EMAIL
    msg['To'] = to_email
    
    body_text = "Hi! I received your mail via Mailo server. I will get back to you shortly. \n\nBest,\nShubhomoy (SGDEV)"
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

    # মেথড ১: পোর্ট ৫৮৭ ট্রাই (STARTTLS)
    try:
        global_memory["smtp_error"] = "Trying Port 587 (STARTTLS)..."
        print("Trying Port 587...")
        with smtplib.SMTP(SMTP_SERVER, 587, timeout=7) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(EMAIL, PASSWORD)
            smtp.sendmail(EMAIL, to_email, msg.as_string())
        global_memory["smtp_error"] = "✅ Successfully sent via Port 587 STARTTLS!"
        return True
    except Exception as e1:
        print(f"Port 587 failed: {e1}")
        
        # মেথড ২: পোর্ট ৪৬৫ ট্রাই (SSL)
        try:
            global_memory["smtp_error"] = f"Port 587 timed out. Now trying Port 465 (SSL)..."
            print("Trying Port 465...")
            with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=7) as smtp:
                smtp.ehlo()
                smtp.login(EMAIL, PASSWORD)
                smtp.sendmail(EMAIL, to_email, msg.as_string())
            global_memory["smtp_error"] = "✅ Successfully sent via Port 465 SSL!"
            return True
        except Exception as e2:
            # মেথড ৩: পোর্ট ২৫২৫ ট্রাই (বিকল্প পোর্ট)
            try:
                global_memory["smtp_error"] = f"Port 465 also failed. Trying Port 2525..."
                print("Trying Port 2525...")
                with smtplib.SMTP(SMTP_SERVER, 2525, timeout=7) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(EMAIL, PASSWORD)
                    smtp.sendmail(EMAIL, to_email, msg.as_string())
                global_memory["smtp_error"] = "✅ Successfully sent via Port 2525!"
                return True
            except Exception as e3:
                final_error = f"🚨 All Ports Timed Out/Blocked by Mailo! P587: {e1} | P465: {e2} | P2525: {e3}"
                print(final_error)
                global_memory["smtp_error"] = final_error
                return False

@app.get("/run")
def check_and_reply_inbox():
    global global_memory
    try:
        # ইনবক্স রিড করার জন্য টাইমআউট বাড়ানো হলো
        socket.setdefaulttimeout(20.0)
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

        # মেলো দিয়ে রিপ্লাই পাঠানো স্টার্ট
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
                <h1>💻 SGDEV Mail Automation Hub (Mailo Anti-Timeout)</h1>
                <p><strong>System Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                
                <h3 style="color: #00ffcc; text-align: left;">🔄 SMTP / Connection Route Log:</h3>
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
