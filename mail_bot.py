import imaplib
import smtplib
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
SMTP_SERVER = "mail.mailo.com"

# Fail loud and early if the password isn't actually present in the environment.
# This is the #1 cause of "nothing happens" — Render env vars not being picked up,
# a typo in the variable name, or the var being set on the wrong service/deploy.
if not PASSWORD:
    print("🚨 CRITICAL: MAILO_PASSWORD environment variable is NOT set or is empty!")
    print("🚨 Check Render → your service → Environment tab. The key must be exactly 'MAILO_PASSWORD'.")
else:
    print(f"✅ MAILO_PASSWORD loaded ({len(PASSWORD)} characters).")

global_memory = {
    "status": "Waiting for cron-job to check inbox...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A",
    "last_error": "None"
}


def send_reply(to_email, original_subject):
    """
    Sends the auto-reply. Returns (success: bool, error_message: str|None)
    instead of silently swallowing failures, so callers can surface real
    diagnostics to the dashboard / logs.
    """
    try:
        msg = email.message.EmailMessage()
        msg.set_content("Hi! I received your mail. I will get back to you shortly. \n\nBest,\nShubhomoy (SGDEV)")

        safe_subject = original_subject if original_subject else "Your Mail"
        safe_subject = str(safe_subject).replace('\r', '').replace('\n', '').strip()
        to_email = str(to_email).replace('\r', '').replace('\n', '').strip()

        msg['Subject'] = f"Re: {safe_subject}"
        msg['From'] = EMAIL
        msg['To'] = to_email

        print(f"Connecting to Mailo SMTP via Port 465 SSL...")
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=30) as smtp:
            smtp.ehlo()
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Reply successfully sent to {to_email} via Mailo SMTP!")
        return True, None

    except smtplib.SMTPAuthenticationError as e:
        err = f"SMTP auth failed — check MAILO_PASSWORD is correct on Render: {e}"
        print(f"🚨 {err}")
        return False, err
    except (smtplib.SMTPException, OSError) as e:
        err = f"SMTP connection/send error: {e}"
        print(f"🚨 {err}")
        return False, err
    except Exception as e:
        err = f"Unexpected error in send_reply: {e}"
        print(f"🚨 {err}")
        return False, err


@app.get("/run")
def check_and_reply_inbox():
    global global_memory

    if not PASSWORD:
        msg = "MAILO_PASSWORD is not set in the environment. Set it on Render → Environment tab."
        global_memory["status"] = "🚨 Config Error"
        global_memory["last_error"] = msg
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        return {"status": "Error", "detail": msg}

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        _, messages = mail.search(None, 'UNSEEN')

        if not messages[0]:
            mail.logout()
            global_memory["status"] = "✅ Checked inbox — no new emails"
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            global_memory["last_error"] = "None"
            return {"status": "Success", "message": "Checked inbox. No new emails."}

        any_failures = []

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = email.message_from_bytes(msg_data[0][1])
            subject = raw_email.get('Subject', 'No Subject')
            sender = raw_email.get("From", "Unknown Sender")

            # Body extraction
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

            body = str(body) if body is not None else ""
            cleaned_body = body.replace('\r\n', '\n').strip()

            success, error_msg = send_reply(sender, subject)
            if not success:
                any_failures.append(f"{sender}: {error_msg}")

            # Mark as seen regardless, so we don't loop on a message that
            # will always fail to reply to (e.g. malformed sender address).
            mail.store(num, '+FLAGS', '\\Seen')

            global_memory = {
                "status": "🔥 New Mail Processed & Replied! 🔥" if success else "⚠️ Mail Processed — Reply FAILED",
                "sender": sender,
                "body": cleaned_body if cleaned_body else "(No text content found)",
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "last_error": error_msg if error_msg else "None"
            }

        mail.logout()

        if any_failures:
            return {"status": "Partial Failure", "failures": any_failures}
        return {"status": "Success", "message": "Emails processed!"}

    except imaplib.IMAP4.error as e:
        err = f"IMAP login/connection error: {e}"
        print(f"🚨 {err}")
        global_memory["status"] = "🚨 IMAP Error"
        global_memory["last_error"] = err
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        return {"status": "Error", "detail": err}
    except Exception as e:
        err = str(e)
        print(f"🚨 Unexpected error in /run: {err}")
        global_memory["status"] = "🚨 Unexpected Error"
        global_memory["last_error"] = err
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        return {"status": "Error", "detail": err}


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
                .meta {{ color: #8b949e; font-size: 0.9em; margin: 15px 0; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; word-break: break-all; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
                .highlight {{ color: #ff007f; font-weight: bold; font-size: 1.1em; }}
                .error-box {{ background: rgba(255, 0, 0, 0.1); border: 1px solid #ff4444; padding: 12px 16px; border-radius: 8px; color: #ff8888; margin-top: 15px; text-align: left; font-family: monospace; font-size: 0.9em; word-break: break-all; }}
                .config-warning {{ background: rgba(255, 165, 0, 0.15); border: 1px solid orange; padding: 12px 16px; border-radius: 8px; color: orange; margin-bottom: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💻 SGDEV Mail Automation Hub</h1>
                {'<div class="config-warning">🚨 MAILO_PASSWORD is not set in the environment! Set it on Render → Environment tab.</div>' if not PASSWORD else ''}
                <p><strong>System Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                <p class="meta"><strong>🕒 Last Updated:</strong> {global_memory['timestamp']}</p>
                <p><strong>📧 Last Sender:</strong> <span class="highlight">{global_memory['sender']}</span></p>
                <div style="text-align: left;">
                    <h3 style="color: #00ffcc;">📄 Received Message:</h3>
                    <div class="body-box">{global_memory['body']}</div>
                </div>
                {f'<div class="error-box"><strong>Last Error:</strong> {global_memory["last_error"]}</div>' if global_memory.get("last_error", "None") != "None" else ''}
            </div>
        </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
