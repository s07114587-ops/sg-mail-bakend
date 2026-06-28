import imaplib
import email
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# FastAPI ইনিশিয়ালাইজেশন
app = FastAPI(title="🔥 Ultimate Mail Automation Backend 🔥")

# IMAP কনফিগারেশন (তোর আসল ইমেইল এবং অ্যাপ পাসওয়ার্ড এখানে দিবি)
IMAP_SERVER = "imap.gmail.com" # জিমেইলের জন্য
EMAIL_ACCOUNT = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"

# গ্লোবাল মেমোরি
latest_email_status = {
    "status": "Waiting for cron-job to trigger...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A"
}

# ইনবক্স চেক করার ফাংশন
def fetch_latest_email():
    global latest_email_status
    try:
        # IMAP সার্ভারে লগিন
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # সব মেইল সার্চ করা (সবচেয়ে নতুনটা শেষে থাকে)
        status, messages = mail.search(None, 'ALL')
        if status == "OK":
            mail_ids = messages[0].split()
            if mail_ids:
                latest_id = mail_ids[-1] # একদম শেষের (নতুন) মেইলটার আইডি
                
                # মেইল ডেটা ফেচ করা
                res, msg_data = mail.fetch(latest_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_email = email.message_from_bytes(response_part[1])
                        
                        sender = raw_email.get("From", "Unknown Sender")
                        
                        # তোর সেই "Huge Brain" ক্র্যাশ-প্রুফ বডি পার্সিং লজিক
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

                        # NoneType এরর চিরতরে শেষ
                        body = str(body) if body is not None else ""
                        cleaned_body = body.replace('\r\n', '\n').strip()

                        # মেমোরিতে ডাটা আপডেট
                        latest_email_status = {
                            "status": "🔥 Inbox Checked & Automation Successful! 🔥",
                            "sender": sender,
                            "body": cleaned_body if cleaned_body else "(No text content found in body)",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                        }
        mail.logout()
    except Exception as e:
        # ক্র্যাশ না করে ড্যাশবোর্ডে এরর দেখাবে
        latest_email_status["status"] = f"IMAP Error: {str(e)}"
        latest_email_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

# GET রিকোয়েস্ট (ব্রাউজার বা Cron-job থেকে আসলে)
@app.get("/run", response_class=HTMLResponse)
async def view_dashboard_and_trigger():
    # ১. প্রথমে মেইল চেক করবে
    fetch_latest_email()
    
    # ২. তারপর আপডেটেড ড্যাশবোর্ড দেখাবে
    html_content = f"""
    <html>
        <head>
            <title>Mail Automation Status</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 40px; }}
                .container {{ max-width: 750px; margin: auto; background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
                h1 {{ color: #58a6ff; border-bottom: 2px solid #21262d; padding-bottom: 10px; margin-top: 0; }}
                .status-badge {{ display: inline-block; padding: 6px 12px; border-radius: 6px; background: #238636; color: white; font-weight: bold; font-size: 0.9em; }}
                .meta {{ color: #8b949e; font-size: 0.9em; margin: 15px 0; }}
                .body-box {{ background: #0d1117; padding: 20px; border-left: 4px solid #58a6ff; font-family: monospace; white-space: pre-wrap; border-radius: 4px; color: #e6edf3; margin-top: 10px; overflow-x: auto; }}
                .highlight {{ color: #ff7b72; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 Master Mail Automation Hub</h1>
                <p><strong>Status:</strong> <span class="status-badge">{latest_email_status['status']}</span></p>
                <p class="meta"><strong>🕒 Last Checked/Updated:</strong> {latest_email_status['timestamp']}</p>
                <p><strong>📧 Latest Sender:</strong> <span class="highlight">{latest_email_status['sender']}</span></p>
                <h3>📄 Extracted Email Body:</h3>
                <div class="body-box">{latest_email_status['body']}</div>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
