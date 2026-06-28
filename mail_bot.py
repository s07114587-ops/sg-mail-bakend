from fastapi import FastAPI
import imaplib, email, smtplib, os

app = FastAPI()

def check_and_reply():
    # তোর সেই ইমেইল লজিক এখানে থাকবে
    # ... (আগের কোড) ...
    return "Checked and Replied!"

@app.get("/")
def home():
    return {"status": "Automation is running!"}

@app.get("/run")
def run_automation():
    return {"result": check_and_reply()}
