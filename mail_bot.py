@app.get("/run")
def check_and_reply_inbox():
    global global_memory

    if not PASSWORD:
        msg = "MAILO_PASSWORD is not set in the environment."
        global_memory["status"] = "🚨 Config Error"
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
            return {"status": "Success", "message": "Checked inbox. No new emails."}

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = email.message_from_bytes(msg_data[0][1])
            subject = raw_email.get('Subject', 'No Subject')
            sender = raw_email.get("From", "Unknown Sender")

            # সাধারণ টেক্সট বডি এক্সট্রাক্ট (কোনো পিজিপি ডিক্রিপশন ছাড়া)
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

            cleaned_body = str(body).strip()

            # অটো-রিপ্লাই পাঠানো
            success, error_msg = send_reply(sender, subject)
            mail.store(num, '+FLAGS', '\\Seen')

            global_memory = {
                "status": "🔥 New Mail Processed & Replied! 🔥" if success else "⚠️ Reply FAILED",
                "sender": sender,
                "body": cleaned_body if cleaned_body else "(No text content found)",
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "last_error": error_msg if error_msg else "None"
            }

        mail.logout()
        return {"status": "Success", "message": "Emails processed!"}

    except Exception as e:
        return {"status": "Error", "detail": str(e)}
