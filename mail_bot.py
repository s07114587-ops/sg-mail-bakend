@app.get("/run")
def check_and_reply_cron():
    global global_memory
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=20)
        mail.login(EMAIL, MAILO_PASSWORD)
        mail.select("inbox")

        # ১. শুধু আনরেড মেইল খোঁজা
        _, messages = mail.search(None, 'UNREAD')
        
        # 🎯 ওটিপি বা খালি ইনবক্সের বাগ ফিক্স: মেইল না থাকলে এখানেই স্টপ হবে
        if not messages[0] or messages[0].strip() == b'':
            mail.logout()
            global_memory["status"] = "🟢 Checked: No New Unread Mails."
            global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            return {"status": "Success", "message": "No new unread mails."}

        mail_ids = messages[0].split()
        if len(mail_ids) == 0:
            mail.logout()
            global_memory["status"] = "🟢 Checked: Zero Unread Mails."
            return {"status": "Success", "message": "Inbox clear."}

        latest_mail_id = mail_ids[-1] 

        _, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
        raw_email = email.message_from_bytes(msg_data[0][1])
        
        subject = raw_email.get('Subject', 'No Subject')
        sender = raw_email.get("From", "Unknown Sender")

        email_finder = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        clean_sender = email_finder.group(0) if email_finder else sender

        # ব্রেভো দিয়ে অটো-রিপ্লাই ফায়ার
        reply_success = send_brevo_api_reply(clean_sender, subject)

        # রিপ্লাই সাকসেস হলে ওটাকে রিড মার্ক করা
        if reply_success:
            mail.store(latest_mail_id, '+FLAGS', '\\Seen')

        global_memory["status"] = "🚀 SGDEV Brevo System Synchronized!"
        global_memory["sender"] = clean_sender
        global_memory["subject"] = subject
        global_memory["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        mail.logout()
        return {"status": "Synced", "auto_reply": global_memory["reply_status"]}

    except Exception as e:
        global_memory["status"] = f"🚨 Sync Error: {str(e)}"
        return {"status": "Error", "detail": str(e)}
