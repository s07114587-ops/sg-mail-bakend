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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = "sgdev@netc.fr"
MAILO_PASSWORD = os.getenv('MAILO_PASSWORD') 
IMAP_SERVER = "mail.mailo.com"
BREVO_API_KEY = os.getenv('BREVO_API_KEY')

global_memory = {
    "status": "🟢 System Idle. Waiting for New Mails...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet."
}

def send_brevo_api_reply(to_email, original_subject):
    global global_memory
    if not BREVO_API_KEY:
        global_memory["reply_status"] = "🚨 Error: BREVO_API_KEY is missing!"
        return False
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        
        body_text = (
            f"Hi!\n\n"
            f"We received your mail regarding '{clean_subject}'.\n"
            f"Thanks for mailing us. Have a nice day!\n\n"
            f"🇮🇳 Proudly from India 🇮🇳\n\n"
            f"--- Our Profiles & Main Web ---\n"
            f"🌐 Main Website: https://shubhomoy.dnc.su/\n"
            f"📧 Contact Email: s07114587@gmail.com\n"
            f"🎨 DeviantArt: https://www.deviantart.com/sgdev111\n"
            f"💼 Behance: https://www.behance.net/sgdev1\n"
            f"💻 Dev.to: https://dev.to/sgdev_sg_dev\n"
            f"🤖 Reddit: https://www.reddit.com/user/sgdev111\n\n"
            f"Best Regards,\n"
            f"SGDEV Team"
        )

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "sender": {"name": "SGDEV Bot", "email": "sgdev@netc.fr"},
            "to": [{"email": clean_to}],
            "subject": f"Re: {clean_subject}",
            "textContent": body_text
        }

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
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, MAILO_PASSWORD)
        mail.select("inbox")

        # ১. ইনবক্সে শুধু আনরেড মেইল খোঁজা
        _, messages = mail.search(None, 'UNREAD')
        
        # 🎯 মেইন ফিক্স: যদি কোনো মেইল আইডি না পাওয়া যায়, তবে কোনো FETCH হবে না
        if not messages or not messages[0] or messages[0].strip() == b'':
            mail.logout()
            global_memory["status"] = "🟢 Checked: No New Unread Mails."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "Inbox is completely clean. No new unread mails."}

        mail_ids = messages[0].split()
        
        # আরেকটি ব্যাকআপ সিকিউরিটি চেক যদি লিস্ট খালি থাকে
        if len(mail_ids) == 0:
            mail.logout()
            global_memory["status"] = "🟢 Checked: Zero Unread Mails."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "Inbox clear."}

        # এখন লিস্টে মেইল থাকা গ্যারান্টিড, তাই FETCH সেফলি কাজ করবে
        latest_mail_id = mail_ids[-1] 

        _, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
        raw_email = email.message_from_bytes(msg_data[0][1])
        
        subject = raw_email.get('Subject', 'No Subject')
        sender = raw_email.get("From", "Unknown Sender")

        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # ব্রেভো দিয়ে অটো-রিপ্লাই ফায়ার
        reply_success = send_brevo_api_reply(clean_sender, subject)

        # রিপ্লাই সফল হলে মেইলটাকে সাথে সাথে 'Read' করে দেওয়া
        if reply_success:
            mail.store(latest_mail_id, '+FLAGS', '\\Seen')

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
