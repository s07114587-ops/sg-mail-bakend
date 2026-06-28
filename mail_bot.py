import email
from fastapi import FastAPI, Request
import uvicorn

# Initialize FastAPI
app = FastAPI()

# Accepting both GET and POST so it doesn't crash when you test in the browser
@app.api_route("/run", methods=["GET", "POST"])
async def process_email(request: Request):
    try:
        # 1. Grab raw payload (Works for SendGrid/Mailgun POST webhooks)
        raw_data = await request.body()
        
        # 2. Guard clause: If you visit via browser (GET), raw_data is empty
        if not raw_data:
            return {
                "status": "Success", 
                "message": "Endpoint is active, but no email payload was received. Send a POST request."
            }

        # 3. Parse the email bytes into an email message object
        raw_email = email.message_from_bytes(raw_data)
        
        # 4. Safely extract sender (Use .get to avoid KeyErrors)
        sender = raw_email.get("From", "Unknown Sender")
        
        # 5. Core Logic: Extract Body Safely
        body = ""
        if raw_email.is_multipart():
            for part in raw_email.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        # Use errors='ignore' to prevent UnicodeDecodeError on weird characters
                        body = payload.decode('utf-8', errors='ignore')
                        break # Found the text, stop looping
        else:
            payload = raw_email.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')

        # 6. THE FIX FOR YOUR SCREENSHOT:
        # Force 'body' to be a string even if something went wildly wrong above
        body = str(body) if body is not None else ""

        # Now you can safely use .replace() because it is 100% guaranteed to be a string
        cleaned_body = body.replace('\r\n', ' ').strip()

        # 7. Execute your print statement
        print(f"Received from {sender}: {cleaned_body[:50]}") 

        return {
            "status": "Success", 
            "sender": sender, 
            "body_preview": cleaned_body[:50]
        }

    except Exception as e:
        # If any other error happens, it returns cleanly instead of throwing a 500 Server Error
        return {"status": "Error", "detail": str(e)}

# Run with Uvicorn
if __name__ == "__main__":
    # Run this using: python filename.py
    uvicorn.run("filename:app", host="0.0.0.0", port=8000, reload=True)
