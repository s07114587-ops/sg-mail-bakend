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

app = FastAPI(title="💻 SGDEV Mailo Auto-Login Engine 💻")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📧 মেলো ক্রেডেনশিয়ালস (রেন্ডার এনভায়রনমেন্ট থেকে আসবে)
EMAIL = "sgdev@netc.fr"
MAILO_PASSWORD = os.getenv('MAILO_PASSWORD')
IMAP_SERVER = "mail.mailo.com"

global_memory = {
    "status": "🟢 System Idle. Waiting for Cron Job...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet."
}

def send_mailo_auto_session_reply(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic secure reply from SGDEV Mailo Engine.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 🌐 ১. একটি লাইভ সেশন তৈরি করা (যা কুকি ধরে রাখবে)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.mailo.com/"
        })

        # 🔐 ২. কোডের ভেতর মেলো পোর্টালে ব্যাকএন্ড লগইন ট্রিগার
        login_url = "https://www.mailo.com/mailo/app/login.php"
        login_data = {
            "login": EMAIL,
            "password": MAILO_PASSWORD,
            "action": "login",
            "stay_logged": "1"
        }
        
        # লগইন রিকোয়েস্ট পাঠানো (মেলো এখানে আমাদের সেশন কুকি দিয়ে দেবে)
        login_res = session.post(login_url, data=login_data, timeout=15)
        
        # 📨 ৩. সেই লাইভ সেশন কুকি ব্যবহার করে মেইল পাঠানো
        send_url = "https://www.mailo.com/mailo/app/send_mail.php"
        mail_payload = {
            "to": clean_to,
            "subject": f"Re: {clean_subject}",
            "body": body_text,
            "submit": "Send",
            "from_ajax": "1"
        }
        
        send_res = session.post(send_url, data=mail_payload, timeout=15)
        
        # 📊 ৪. ভেরিফিকেশন চেক
        if send_res.status_code == 200:
            global_memory["reply_status"] = f"✅ SUCCESS! Generated Auto-Session & Sent to {clean_to}!"
            return True
        else:
            global_memory["reply_status"] = f"⚠️ Mailo Gateway Rejected (Status: {send_res.status_code})"
            return False

    except Exception as e:
        global_memory["reply_status"] = f"🚨 Auto-Session Error: {str(e)}"
        return False

@app.get("/run")
def check_and_reply_cron():
    global global_memory
    try:
        # ইনবক্স চেক করা
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

        # ক্লিন ইমেইল আইডি বের করা
        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # কাস্টম অটো-লগইন রিপ্লাই ট্রিগার
        send_mailo_auto_session_reply(clean_sender, subject)

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
            <title>SGDEV Mailo Engine Tracker</title>
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
                <h1>💻 SGDEV Mailo Auto-Session Engine</h1>
                
                <div class="status-box">
                    <strong>SYSTEM LOG:</strong> {global_memory['status']}
                </div>

                <div class="reply-box">
                    <strong>📩 AUTOMATION OUTPUT:</strong> {global_memory['reply_status']}
                </div>

                <table class="log-table">
                    <tr>
                        <th>Metric</th>
                        <th>Live Server Data</th>
                    </tr>
                    <tr>
                        <td>👤 Last Sender User</td>
                        <td class="highlight">{global_memory['sender']}</td>
                    </tr>
                    <tr>
                        <td>📄 Mail Subject</td>
                        <td>{global_memory['subject']}</td>
                    </tr>
                    <tr>
                        <td>🕒 Last Cron Refresh</td>
                        <td style="color: #00ffcc;">{global_memory['timestamp']}</td>
                    </tr>
                </table>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
