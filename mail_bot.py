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

# 🔥 ১০০০ IQ ট্রিক: মেলো-র ৩টি আলাদা আলাদা SMTP হোস্ট ট্রাই করা হবে ব্লক ভাঙার জন্য
SMTP_SERVERS = ["mail.mailo.com", "smtp.mailo.com", "smtp.netc.fr"]

global_memory = {
    "status": "Waiting for /run...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A",
    "smtp_error": "No errors tracked yet."
}

def send_reply(to_email, original_subject):
    global global_memory
    socket.setdefaulttimeout(6.0) # ফাস্ট রেসপন্স টাইমআউট
    
    msg = MIMEMultipart()
    safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
    to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

    msg['Subject'] = f"Re: {safe_subject}"
    msg['From'] = EMAIL
    msg['To'] = to_email
    
    body_text = "Hi! I received your mail via Mailo server. I will get back to you shortly. \n\nBest,\nShubhomoy (SGDEV)"
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

    # লুপ চালিয়ে সবকটি মেলো হোস্ট চেক করা হবে
    for server in SMTP_SERVERS:
        # প্রথমে চেষ্টা করবো সিকিউর SSL পোর্ট ৪৬৫
        try:
            print(f"Trying {server} via Port 465 SSL...")
            global_memory["smtp_error"] = f"Trying {server} : 465..."
            with smtplib.SMTP_SSL(server, 465, timeout=6) as smtp:
                smtp.ehlo()
                smtp.login(EMAIL, PASSWORD)
                smtp.sendmail(EMAIL, to_email, msg.as_string())
            global_memory["smtp_error"] = f"✅ Success via {server} (Port 465)!"
            return True
        except Exception:
            # ৪৬৫ ফেল করলে চেষ্টা করবো পোর্ট ৫৮৭
            try:
                print(f"Trying {server} via Port 587 STARTTLS...")
                global_memory["smtp_error"] = f"Trying {server} : 587..."
                with smtplib.SMTP(server, 587, timeout=6) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(EMAIL, PASSWORD)
                    smtp.sendmail(EMAIL, to_email, msg.as_string())
                global_memory["smtp_error"] = f"✅ Success via {server} (Port 587)!"
                return True
            except Exception:
                continue # এই হোস্ট সম্পূর্ণ ফেল করলে পরের হোস্টে যাবে
                
    # সব হোস্ট ফেল করলে ফাইনাল মেসেজ
    final_error = "🚨 Mailo has totally blocked Render IPs on all hosts/ports!"
    global_memory["smtp_error"] = final_error
    print(final_error)
    return False

@app.get("/run")
def check_and_reply_inbox():
    global global_memory
    try:
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

        # রিপ্লাই লুপ স্টার্ট
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
                <h1>💻 SGDEV Mail Automation Hub (Multi-Host Mode)</h1>
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
