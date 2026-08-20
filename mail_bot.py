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

# 🎯 প্রথমে এই REGEX দিয়ে চেক হবে: noreply, no-reply, noreply2, no_reply123 ইত্যাদি
# যেকোনো সংখ্যা/সাফিক্স থাকলেও ধরবে, কারণ \d* এবং word boundary ইউজ করা হয়েছে
NOREPLY_PATTERN = re.compile(r'no[-_]?reply\d*', re.IGNORECASE)

# 🎯 এই লিস্টে যেসব sender থাকবে, তাদের কখনোই অটো-রিপ্লাই পাঠানো হবে না।
# চাইলে নিচে আরও keyword/domain অ্যাড করতে পারবে।
SKIP_SENDER_KEYWORDS = [
    "deviantart",
    "support",
    "donotreply",
    "do-not-reply",
    "mailer-daemon",
    "postmaster",
    # 🎯 নতুন যোগ করা keywords/domains
    "inc.eu.org",
    "eu.org",
    "cloudflare",
    "brevo",
    "clouddns",
    "cloud-dns",
    "dns.google",
]

# লাইভ ট্র্যাকিং মেমোরি (লাস্ট প্রসেসড মেইল আইডি মনে রাখার জন্য)
global_memory = {
    "status": "🟢 System Idle. Waiting for New Mails...",
    "sender": "No Mail Checked Yet",
    "subject": "N/A",
    "timestamp": "N/A",
    "reply_status": "No reply triggered yet.",
    "last_processed_msg_id": ""  # এখানে ইউনিক আইডি সেভ থাকবে
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
            f"🌐 Main Website: https://shubhomoy.vercel.app/\n"
            f"📧 Contact Email: sgdev@netc.fr\n"
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


def get_skip_reason(sender_lower: str):
    """
    🎯 প্রথমে noreply-প্যাটার্ন চেক করে (noreply, no-reply, noreply2, no_reply9 ইত্যাদি)।
    তারপর SKIP_SENDER_KEYWORDS লিস্টের বাকি কিওয়ার্ডগুলো চেক করে।
    ম্যাচ পেলে reason string রিটার্ন করে, নাহলে None রিটার্ন করে।
    """
    # ধাপ ১: noreply প্যাটার্ন (সবচেয়ে হাই প্রায়োরিটি)
    match = NOREPLY_PATTERN.search(sender_lower)
    if match:
        return match.group(0)

    # ধাপ ২: বাকি কিওয়ার্ড লিস্ট
    for kw in SKIP_SENDER_KEYWORDS:
        if kw in sender_lower:
            return kw

    return None


@app.get("/run")
def check_and_reply_cron():
    global global_memory
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, MAILO_PASSWORD)
        mail.select("inbox")

        # 🎯 আমরা সব মেইল খুঁজবো, আনরেডের ঝামেলা শেষ!
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK' or not messages or not messages[0].strip():
            mail.logout()
            global_memory["status"] = "🟢 Checked: Inbox Empty."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "Inbox clear."}

        mail_ids = messages[0].split()
        if len(mail_ids) == 0:
            mail.logout()
            global_memory["status"] = "🟢 Checked: Zero Mails."
            return {"status": "Success"}

        latest_mail_id = mail_ids[-1] 

        fetch_status, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
        if fetch_status != 'OK' or not msg_data or not msg_data[0]:
            mail.logout()
            return {"status": "Error", "message": "Fetch failed"}

        raw_email = email.message_from_bytes(msg_data[0][1])
        
        # 🎯 মেইলের ইউনিক মেসেজ আইডি নেওয়া হচ্ছে
        msg_id = raw_email.get('Message-ID', str(latest_mail_id))

        # 🎯 যদি এই মেইলটা অলরেডি আগের ক্রনজবে প্রসেস হয়ে থাকে, তবে স্কিপ করো!
        if global_memory["last_processed_msg_id"] == msg_id:
            mail.logout()
            global_memory["status"] = "🟢 Checked: No New Mail Received (Skipped Old)."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "Already replied to this mail. Skipping."}

        subject = raw_email.get('Subject', 'No Subject')
        sender = raw_email.get("From", "Unknown Sender")

        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # 🛑 ফিল্টার: প্রথমে noreply-টাইপ চেক, তারপর বাকি কিওয়ার্ড লিস্ট
        sender_lower = clean_sender.lower()
        matched_skip_keyword = get_skip_reason(sender_lower)

        if matched_skip_keyword:
            # মেইলটা প্রসেসড বলে মার্ক করে দিচ্ছি, যাতে বারবার লুপ না হয়
            global_memory["last_processed_msg_id"] = msg_id
            global_memory["status"] = f"🟢 Skipped '{matched_skip_keyword}' Mail from: {clean_sender}"
            global_memory["sender"] = clean_sender
            global_memory["subject"] = subject
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            global_memory["reply_status"] = f"🚫 Auto-reply skipped ('{matched_skip_keyword}' sender detected)."
            mail.logout()
            return {"status": "Success", "message": f"'{matched_skip_keyword}' sender detected. Skipped auto-reply."}

        # সাধারণ মেইল হলে ব্রেভো দিয়ে রিপ্লাই পাঠানো
        reply_success = send_brevo_api_reply(clean_sender, subject)

        if reply_success:
            # 🎯 সফল হলে এই মেইলের আইডি মেমোরিতে লক করে দাও
            global_memory["last_processed_msg_id"] = msg_id

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
