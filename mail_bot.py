import imaplib
import email
import os
import re
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware 
from playwright.sync_api import sync_playwright
import uvicorn

app = FastAPI(title="💻 SGDEV Playwright Browser Engine 💻")

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

def send_hacker_browser_reply(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic secure reply via SGDEV Browser Automation.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 🚀 ব্যাকগ্রাউন্ডে আসল ক্রোমিয়াম ব্রাউজার লঞ্চ করা (ফায়ারওয়াল বাইপাস)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # ১. সরাসরি মেলো লগইন পেজে যাওয়া
            page.goto("https://www.mailo.com/mailo/app/login.php", timeout=30000)
            
            # ২. মানুষের মতো টাইপ করে লগইন করা
            page.fill("input[name='login']", EMAIL)
            page.fill("input[name='password']", MAILO_PASSWORD)
            page.click("input[type='submit']")
            page.wait_for_timeout(3000)  # সেশন লোড হতে ৩ সেকেন্ড ওয়েট
            
            # ৩. মেইল কম্পোজ পেজে চলে যাওয়া
            page.goto("https://www.mailo.com/mailo/app/mail.php?page=compose", timeout=30000)
            
            # ৪. মেইল ফর্ম ফিলাপ করে সেন্ড করা
            page.fill("input[name='to']", clean_to)
            page.fill("input[name='subject']", f"Re: {clean_subject}")
            page.fill("textarea[name='body']", body_text)
            
            page.click("input[name='submit']")  # সেন্ড বাটনে ফাইনাল ক্লিক!
            page.wait_for_timeout(2000)
            
            browser.close()
            
        global_memory["reply_status"] = f"✅ HACK SUCCESS! Playwright Browser delivered mail to {clean_to}!"
        return True

    except Exception as e:
        global_memory["reply_status"] = f"🚨 Browser Engine Error: {str(e)}"
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

        # ইমেইল আইডি ফিল্টার করা
        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # প্লে-রাইট ব্রাউজার অটোমেশন দিয়ে মেইল পাঠানো
        send_hacker_browser_reply(clean_sender, subject)

        global_memory["status"] = "🚀 SGDEV Browser Sync Complete!"
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
            <title>SGDEV Playwright Tracker</title>
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
                <h1>🎮 SGDEV Playwright Browser Automation</h1>
                
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
