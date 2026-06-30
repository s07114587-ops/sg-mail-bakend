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

# পাসওয়ার্ড লোড হয়েছে কিনা তা চেক করা
if not PASSWORD:
    print("🚨 CRITICAL: MAILO_PASSWORD environment variable is NOT set or is empty!")
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
    Port 587 (STARTTLS) ব্যবহার করে অটো-রিপ্লাই পাঠানোর ফাংশন
    """
    try:
        msg = email.message.EmailMessage()
        msg.set_content("Hi! I received your mail. I
