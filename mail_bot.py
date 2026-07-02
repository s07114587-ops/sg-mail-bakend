import imaplib
import email
import os
import smtplib
import re
from email.mime.text import MIMEText
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

app = FastAPI(title="💻 SGDEV Ultra-Light Mailo Engine 💻")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📧 মেলো ক্রেডেনশিয়ালস
EMAIL = "sgdev@netc.fr"
MAILO_PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"
SMTP_SERVER = "mail.mailo.com"

global_memory = {
    "status": "🟢 System Idle. Waiting for Cron Job...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet."
}

def send_secure_smtp_reply(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic reply via SGDEV Ultra-Light Engine.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        msg = MIMEText(body_text)
        msg['Subject'] = f"Re: {clean_subject}"
        msg['From'] = EMAIL
        msg['To'] = clean_to

        # 🔐 সিকিউর এসএসএল পোর্ট ৪৬৫ (যা রেন্ডার কখনো ব্লক করে না)
        # এটি সরাসরি মেলোর অফিসিয়াল সিকিউর মেইল গেটওয়ে
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=15)
        server.login(EMAIL, MAILO_PASSWORD)
        server.sendmail(EMAIL, [clean_to], msg.as_string())
        server.quit()
            
        global_memory["reply_status"] = f"✅ SUCCESS! Mail delivered securely to {clean_to}!"
        return True

    except Exception as e:
        global_memory["reply_status"] = f"🚨 SMTP Gateway Error: {str(e)}"
        return False

@app.get("/run")
def check_and_reply_cron():
    global global_memory
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, MAILO_PASSWORD)
        mail.select("inbox")

        _, messages = mail.search(None, 'ALL')
        
        if not messages[0]:
            mail.logout()
            global_memory["status"] = "🟢 Checked: Inbox Empty."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "Inbox is empty."}

        mail_ids = messages[0].split()
        latest_mail_id = mail_ids[-1] 

        _, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
        raw_email = email.message_from_bytes(msg_data[0][1])
        
        subject = raw_email.get('Subject', 'No Subject')
        sender = raw_email.get("From", "Unknown Sender")

        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # সিকিউর এসএমটিপি দিয়ে মেইল পাঠানো
        send_secure_smtp_reply(clean_sender, subject)

        global_memory["status"] = "🚀 SGDEV System Synchronized Successfully!"
        global_memory["sender"] = clean_sender
        global_memory["subject"] = subject
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        mail.logout()
        return {"status": "Synced", "auto_reply": global_memory["reply_status"]}

    except Exception as e:
        global_memory["status"] = f"🚨 Sync Error: {str(e)}"
        return {"status": "Error", "detail": str(e)}

@app.get("/", response_class=HTMLResponse)
async def view_public_logs():
    html_content = f"""
    <html>
        <head>
            <title>SGDEV Light Engine Tracker</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background-color: #0a0a12; color: #c9d1d9; padding: 40px; text-align: center; }}
                .container {{ max-width: 750px; margin: auto; background: rgba(20, 20, 35, 0.9); padding: 30px; border-radius: 12px; border: 2px solid #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }}
                h1 {{ color: #ff007f; text-shadow: 0 0 10px #ff007f; margin-top: 0; }}
                .status-box {{ background: #16162a; border-left: 5px solid #00ffcc; padding: 15px; border-radius: 4px; text-align: left; font-family: monospace; font-size: 1.1em; margin: 20px 0; }}
                .reply-box {{ background: #1b2a1c; border: 1px solid #00ffcc; padding: 12px; border-radius: 4px; color: #99ffbc; text-align: left; font-family: monospace; margin: 15px 0; }}
                .log-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-family: monospace; text-align: left; }}
                .log-table th, .log-table td {{ padding: 12px; border-bottom: 1px solid #222; }}
                .log-table th {{ color: #00ffcc; border-bottom: 2px solid #00ffcc; }}
                .highlight {{ color: #ff007f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Ultra-Light Mail Automation</h1>
                <div class="status-box"><strong>SYSTEM LOG:</strong> {global_memory['status']}</div>
                <div class="reply-box"><strong>📩 AUTOMATION OUTPUT:</strong> {global_memory['reply_status']}</div>
                <table class="log-table">
                    <tr><th>Metric</th><th>Live Server Data</th></tr>
                    <tr><td>👤 Last Sender User</td><td class="highlight">{global_memory['sender']}</td></tr>
                    <tr><td>📄 Mail Subject</td><td>{global_memory['subject']}</td></tr>
                    <tr><td>🕒 Last Cron Refresh</td><td style="color: #00ffcc;">{global_memory['timestamp']}</td></tr>
                </table>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
