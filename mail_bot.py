import imaplib
import email
import os
import requests  # SMTP-র বদলে HTTP রিকোয়েস্ট দিয়ে মেইল পাঠানোর ওস্তাদ লাইব্রেরি
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

global_memory = {
    "status": "Waiting for /run...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A",
    "smtp_error": "No errors tracked yet."
}

def send_reply_via_mailo_web(to_email, original_subject):
    global global_memory
    try:
        global_memory["smtp_error"] = "Initiating Mailo Webmail Request..."
        
        safe_subject = str(original_subject if original_subject else "Your Mail").replace('\r', '').replace('\n', '').strip()
        to_email = str(to_email).replace('\r', '').replace('\n', '').strip()
        body_text = "Hi! I received your mail via Mailo server. (Bypassed via Webmail Protocol) \n\nBest,\nShubhomoy (SGDEV)"

        # 🔥 ১০০০ IQ মেলো ওয়েবমেইল বাইপাস সেশন
        session = requests.Session()
        
        # স্টেপ ১: মেলো লগইন পেজে হিট করে অথেনটিকেশন নেওয়া
        login_url = "https://www.mailo.com/mailo/app/login.php"
        login_data = {
            "login": EMAIL,
            "password": PASSWORD,
            "action": "login"
        }
        
        global_memory["smtp_error"] = "Logging into Mailo via HTTP..."
        response = session.post(login_url, data=login_data, timeout=15)
        
        # স্টেপ ২: লগইন সাকসেস হলে মেলো-র নিজস্ব আউটগোয়িং গেটওয়ে দিয়ে মেইল শুট করা
        send_url = "https://www.mailo.com/mailo/app/send_mail.php"
        mail_payload = {
            "to": to_email,
            "subject": f"Re: {safe_subject}",
            "body": body_text,
            "submit": "send"
        }
        
        global_memory["smtp_error"] = "Sending message through Mailo Web-Gate..."
        send_response = session.post(send_url, data=mail_payload, timeout=15)
        
        if send_response.status_code == 200:
            global_memory["smtp_error"] = "✅ SUCCESS! Mailo Webmail bypassed the SMTP block permanently!"
            print("Mail sent successfully via Web Gate!")
            return True
        else:
            raise Exception(f"Mailo responded with status code {send_response.status_code}")

    except Exception as e:
        final_error = f"🚨 Mailo Web Bypass Failed: {e}"
        print(final_error)
        global_memory["smtp_error"] = final_error
        return False

@app.get("/run")
def check_and_reply_inbox():
    global global_memory
    try:
        # মেলো থেকে ইনবক্স রিড করা (IMAP)
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

        # মেলো-র ওয়েব মেথড দিয়ে রিপ্লাই ট্রিগার
        send_reply_via_mailo_web(sender, subject)

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
                .error-box {{ background: #1b2a22; border: 1px solid #00ffcc; padding: 15px; border-radius: 6px; color: #99ffbc; margin: 15px 0; font-family: monospace; text-align: left; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; word-break: break-all; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Mail Automation Hub (Mailo Web-Bypass)</h1>
                <p><strong>System Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                
                <h3 style="color: #00ffcc; text-align: left;">🔄 Web Route Log:</h3>
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
