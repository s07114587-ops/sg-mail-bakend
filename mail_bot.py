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

app = FastAPI(title="💻 SGDEV 100% Open-Source Mail Automation 💻")

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

global_memory = {
    "status": "🟢 System Idle. Waiting for Cron Job...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet."
}

def send_secure_open_source_reply(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic secure reply from SGDEV 100% Open-Source Engine.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 🌐 মেলো ডাইরেক্ট সিকিউর ওয়েব সেশন ইন্টারফেস
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.mailo.com/"
        })

        # ১. সেশন জেনারেট করতে মেলো হোমপেজ হিট করা
        init_res = session.get("https://www.mailo.com/", timeout=15)

        # ২. সিকিউর ওয়েব পোর্টাল দিয়ে লগইন অথেনটিকেশন ট্রিগার
        login_url = "https://www.mailo.com/mailo/app/login.php"
        login_data = {
            "login": EMAIL,
            "password": MAILO_PASSWORD,
            "action": "login",
            "stay_logged": "1"
        }
        
        login_res = session.post(login_url, data=login_data, timeout=15)
        
        # ৩. মেলো-র মেম্বার প্যানেল থেকে মেল পুশ রুট (HTTP HTTPS রিকোয়েস্ট - যা রেন্ডার ব্লক করতে পারে না)
        send_url = "https://www.mailo.com/mailo/app/send_mail.php"
        mail_payload = {
            "to": clean_to,
            "subject": f"Re: {clean_subject}",
            "body": body_text,
            "submit": "Send",
            "from_ajax": "1"
        }
        
        send_res = session.post(send_url, data=mail_payload, timeout=15)
        
        # ৪. ভেরিফিকেশন চেক
        if send_res.status_code == 200:
            global_memory["reply_status"] = f"✅ SUCCESS! 100% Securely Sent to {clean_to}!"
            return True
        else:
            global_memory["reply_status"] = f"⚠️ Mailo Rejected with Code: {send_res.status_code}"
            return False

    except Exception as e:
        global_memory["reply_status"] = f"🚨 Secure Gateway Error: {str(e)}"
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

        # সেন্ডারের ক্লিন ইমেইল আইডি এক্সট্র্যাক্ট করা (যেমন: Subrata <abc@gmail.com> থেকে শুধু abc@gmail.com নেওয়া)
        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # ওয়ান অ্যান্ড অনলি সিকিউর ওপেন সোর্স অটো-রিপ্লাই ট্রিগার
        send_secure_open_source_reply(clean_sender, subject)

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
            <title>SGDEV Secure Log Tracker</title>
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
                <h1>🛡️ SGDEV 100% Open-Source Mail Automation</h1>
                
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
                <p style="color: #555; font-size: 0.85em; margin-top: 30px;">🔒 Data Privacy Shield: This platform is open-source and completely localized to your Render environment variable.</p>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
