import imaplib
import email
import os
import requests
import re
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

app = FastAPI(title="💻 SGDEV Brevo Global Engine 💻")

# CORS পলিসি ওপেন রাখা হলো যাতে রেন্ডার সার্ভার ফ্রিলি কাজ করতে পারে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📧 মেলো এবং ব্রেভো ক্রেডেনশিয়ালস (Render Environment থেকে রিড হবে)
EMAIL = "sgdev@netc.fr"
MAILO_PASSWORD = os.getenv('MAILO_PASSWORD') 
IMAP_SERVER = "mail.mailo.com"
BREVO_API_KEY = os.getenv('BREVO_API_KEY')

# লাইভ ট্র্যাকিং মেমোরি
global_memory = {
    "status": "🟢 System Idle. Waiting for Cron Job...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet."
}

def send_brevo_api_reply(to_email, original_subject):
    global global_memory
    if not BREVO_API_KEY:
        global_memory["reply_status"] = "🚨 Error: BREVO_API_KEY is missing in Render Environment!"
        return False
    try:
        # মেইল ফিল্ড ক্লিন করা
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        
        # অটো-রিপ্লাই মেসেজ বডি
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic secure reply via SGDEV Brevo Global Engine.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 🚀 ব্রেভো গ্লোবাল এপিআই এন্ডপয়েন্ট (যা সারা বিশ্বের জন্য ডোমেইন ছাড়া কাজ করে)
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "sender": {"name": "SGDEV Bot", "email": "sgdev@netc.fr"}, # ব্রেভোতে তোর ভেরিফাইড প্রেরক মেইল
            "to": [{"email": clean_to}],
            "subject": f"Re: {clean_subject}",
            "textContent": body_text
        }

        # এপিআই পোস্ট রিকোয়েস্ট
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code in [200, 201, 202]:
            global_memory["reply_status"] = f"✅ SUCCESS! Brevo delivered mail to {clean_to}!"
            return True
        else:
            global_memory["reply_status"] = f"⚠️ Brevo API Rejected: {response.text}"
            return False

    except Exception as e:
        global_memory["reply_status"] = f"🚨 Brevo Gateway Error: {str(e)}"
        return False

@app.get("/run")
def check_and_reply_cron():
    global global_memory
    try:
        # মেলো আইম্যাপ সার্ভারে লগইন
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

        # সেন্ডারের মেইল আইডি ক্লিন করা
        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # ব্রেভো গ্লোবাল এপিআই দিয়ে অটো-রিপ্লাই ফায়ার করা
        send_brevo_api_reply(clean_sender, subject)

        global_memory["status"] = "🚀 SGDEV Brevo System Synchronized!"
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
            <title>SGDEV Brevo Tracker</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background-color: #0a0a12; color: #c9d1d9; padding: 40px; text-align: center; }}
                .container {{ max-width: 750px; margin: auto; background: rgba(20, 20, 35, 0.9); padding: 30px; border-radius: 12px; border: 2px solid #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }}
                h1 {{ color: #00ffcc; text-shadow: 0 0 10px #00ffcc; margin-top: 0; }}
                .status-box {{ background: #16162a; border-left: 5px solid #00ffcc; padding: 15px; border-radius: 4px; text-align: left; font-family: monospace; font-size: 1.1em; margin: 20px 0; }}
                .reply-box {{ background: #1b2a1c; border: 1px solid #00ffcc; padding: 12px; border-radius: 4px; color: #99ffbc; text-align: left; font-family: monospace; margin: 15px 0; }}
                .log-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-family: monospace; text-align: left; }}
                .log-table th, .log-table td {{ padding: 12px; border-bottom: 1px solid #222; }}
                .log-table th {{ color: #ff007f; border-bottom: 2px solid #ff007f; }}
                .highlight {{ color: #ff007f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Global Mail Gateway (Brevo Lifetime API)</h1>
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
