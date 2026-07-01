import imaplib
import email
import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import APIKeyCookie
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

app = FastAPI(title="🔒 SGDEV Secure Mail Vault 🔒")

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

# 🔑 ড্যাশবোর্ড লক পাসওয়ার্ড (রেন্ডার এনভায়রনমেন্ট থেকে আসবে)
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')

# কুকি বেসড সিকিউরিটি সেশন
cookie_sec = APIKeyCookie(name="sgdev_session", auto_error=False)

global_memory = {
    "status": "Waiting for /run...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A"
}

# 🛡️ পাসওয়ার্ড চেক করার সিকিউরিটি ফাংশন
def is_authenticated(session: str = Depends(cookie_sec)):
    if not session or session != "authenticated_success":
        return False
    return True

# 🚪 লগইন পেজ (HTML)
@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = None):
    error_msg = f"<p class='error'>{error}</p>" if error else ""
    html = f"""
    <html>
        <head>
            <title>SGDEV Login</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a12; color: #fff; text-align: center; padding-top: 100px; }}
                .login-box {{ max-width: 400px; margin: auto; background: #141423; padding: 40px; border-radius: 12px; border: 2px solid #ff007f; box-shadow: 0 0 20px rgba(255, 0, 127, 0.2); }}
                h2 {{ color: #00ffcc; text-shadow: 0 0 10px #00ffcc; }}
                input[type="password"] {{ width: 100%; padding: 12px; margin: 20px 0; border-radius: 6px; border: 1px solid #ff007f; background: #000; color: #00ffcc; font-size: 1.1em; text-align: center; }}
                button {{ background: #ff007f; color: white; border: none; padding: 12px 24px; font-size: 1em; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; }}
                button:hover {{ background: #ee006f; box-shadow: 0 0 10px #ff007f; }}
                .error {{ color: #ff3333; font-weight: bold; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>🔒 SGDEV Vault Authentication</h2>
                {error_msg}
                <form action="/login" method="POST">
                    <input type="password" name="password" placeholder="Enter System Password" required autofocus>
                    <button type="submit">Unlock System</button>
                </form>
            </div>
        </body>
    </html>
    """
    return html

# 🔑 লগইন পাসওয়ার্ড ভেরিফিকেশন অ্যাকশন
@app.post("/login")
async def do_login(password: str = status.HTTP_200_OK):
    from fastapi import Form
    @app.post("/login")
    async def handle_login(password: str = Form(...)):
        if password == DASHBOARD_PASSWORD:
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="sgdev_session", value="authenticated_success", httponly=True)
            return response
        return RedirectResponse(url="/login?error=Invalid%20Password", status_code=303)
    return await handle_login(password)

# 🚪 লগআউট রুট
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("sgdev_session")
    return response

# 🔄 মেইল রিড করার ট্র্যাকার রুট (পাসওয়ার্ড প্রোটেক্টেড)
@app.get("/run")
def check_inbox(auth: bool = Depends(is_authenticated)):
    if not auth:
        return RedirectResponse(url="/login")
        
    global global_memory
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, MAILO_PASSWORD)
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

        global_memory["status"] = "🔥 Vault Synchronized 🔥"
        global_memory["sender"] = sender
        global_memory["body"] = cleaned_body if cleaned_body else "(No text content)"
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        mail.logout()
        return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        return {"status": "Error", "detail": str(e)}

# 💻 সিকিউর ড্যাশবোর্ড হাবে হিট (পাসওয়ার্ড ছাড়া কেউ দেখতে পারবে না)
@app.get("/", response_class=HTMLResponse)
async def view_dashboard(auth: bool = Depends(is_authenticated)):
    if not auth:
        return RedirectResponse(url="/login")
        
    html_content = f"""
    <html>
        <head>
            <title>SGDEV Secure Vault</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background-color: #0a0a12; color: #c9d1d9; padding: 40px; text-align: center; }}
                .container {{ max-width: 700px; margin: auto; background: rgba(20, 20, 35, 0.9); padding: 30px; border-radius: 12px; border: 2px solid #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }}
                h1 {{ color: #ff007f; text-shadow: 0 0 10px #ff007f; margin-top: 0; }}
                .status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 6px; background: #00ffcc; color: black; font-weight: bold; }}
                .body-box {{ background: rgba(0, 0, 0, 0.4); padding: 20px; border: 1px solid #ff007f; font-family: monospace; white-space: pre-wrap; word-break: break-all; border-radius: 8px; color: #e6edf3; margin-top: 10px; text-align: left; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #ff007f; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 10px; }}
                .btn-run {{ background: #00ffcc; color: black; }}
                .logout-btn {{ background: #444; color: #fff; float: right; font-size: 0.9em; padding: 5px 10px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/logout" class="logout-btn">🚪 Logout</a>
                <h1>💻 SGDEV Secure Mail Vault</h1>
                <p><strong>Vault Status:</strong> <span class="status-badge">{global_memory['status']}</span></p>
                
                <hr style="border: 1px solid #222; margin: 20px 0;">
                <a href="/run" class="btn btn-run">🔄 Trigger Inbox Refresh (/run)</a>
                
                <p style="text-align: left;"><strong>📧 Sender:</strong> <span style="color: #ff007f; font-weight: bold;">{global_memory['sender']}</span></p>
                <p style="text-align: left;"><strong>🕒 Synced At:</strong> {global_memory['timestamp']}</p>
                
                <div style="text-align: left;">
                    <h3 style="color: #00ffcc;">📄 Secret Message Body:</h3>
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
