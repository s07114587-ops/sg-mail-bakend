import email
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

# FastAPI ইনিশিয়ালাইজেশন
app = FastAPI(title="🔥 Ultimate Mail Automation Backend 🔥")

# গ্লোবাল মেমোরি (মেইলের ডাটা সেভ রাখার জন্য)
# এটাই সেই ১ এবং ০ এর লজিক যা ব্রাউজারে ডাটা ধরে রাখবে!
latest_email_status = {
    "status": "No email received yet. Waiting for cron-job...",
    "sender": "N/A",
    "body": "N/A",
    "timestamp": "N/A"
}

# স্টেপ ৩: ব্রাউজারে ওপেন করলে (GET Request) এই সুন্দর ড্যাশবোর্ড দেখাবে
@app.get("/run", response_class=HTMLResponse)
async def view_dashboard():
    # ব্রাউজারে সরাসরি এরর না দেখিয়ে একটি চমৎকার UI দেখাবে
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
                .body-box {{ background: #0d1117; padding: 20px; border-left: 4px solid #58a6ff; font-family: monospace; white-space: pre-wrap; border-radius: 4px; color: #e6edf3; margin-top: 10px; }}
                .highlight {{ color: #ff7b72; font-weight: bold; }}
            </style>
        </head>
            <div class="container">
                <h1>💻 Mail Automation Dashboard</h1>
                <p><strong>Status:</strong> <span class="status-badge">{latest_email_status['status']}</span></p>
                <p class="meta"><strong>🕒 Last Updated:</strong> {latest_email_status['timestamp']}</p>
                <p><strong>📧 Sender:</strong> <span class="highlight">{latest_email_status['sender']}</span></p>
                <h3>📄 Received Email Body:</h3>
                <div class="body-box">{latest_email_status['body']}</div>
            </div>
        </body>
    </html>
    """
    return html_content

# স্টেপ ২: ক্রন-জব বা ওয়েবহুক যখন মেইল পাঠাবে (POST Request)
@app.post("/run")
async def receive_and_process_email(request: Request):
    global latest_email_status
    try:
        # রিকোয়েস্ট থেকে র-ডাটা নেওয়া
        raw_data = await request.body()
        if not raw_data:
            return {"status": "Error", "detail": "Empty payload received via POST"}

        # ইমেইল পার্স করা
        raw_email = email.message_from_bytes(raw_data)
        sender = raw_email.get("From", "Unknown Sender")
        
        # আপনার দেওয়া লজিকের সুপার-আপগ্রেডেড রূপ (Safe Walk)
        body = ""
        if raw_email.is_multipart():
            for part in raw_email.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore') # এনকোডিং ক্র্যাশ রুখতে errors='ignore'
                        break # টেক্সট পেয়ে গেলে লুপ বন্ধ
        else:
            payload = raw_email.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')

        # ১০০% গ্যারান্টিড স্ট্রিং কনভার্সন (NoneType এরর চিরতরে শেষ)
        body = str(body) if body is not None else ""
        cleaned_body = body.replace('\r\n', '\n').strip()

        # টার্মিনালে চেক করার জন্য প্রিন্ট
        print(f"Received from {sender}: {cleaned_body[:50]}")

        # মেমোরিতে ডাটা আপডেট করা (যা ব্রাউজারে রিফ্লেক্ট হবে)
        latest_email_status = {
            "status": "🔥 Automation Successful! 🔥",
            "sender": sender,
            "body": cleaned_body if cleaned_body else "(No text content found in body)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        }

        return {"status": "Success", "message": "State updated perfectly!"}

    except Exception as e:
        # ব্যাকএন্ড ক্র্যাশ না করে এরর রিটার্ন করবে
        return {"status": "Error", "detail": str(e)}

# উভিকর্ন দিয়ে রান করার কোড
if __name__ == "__main__":
    # আপনার ফাইলের নাম যদি main.py হয়, তবে এখানে "main:app" রাখুন
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
