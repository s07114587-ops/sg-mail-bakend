def send_official_mailo_api(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'. This is an automatic secure reply from SGDEV Cloud Engine.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 💡 ডাইরেক্ট মেলো জেনুইন ওয়েব পুশ গেটওয়ে (যেহেতু api.mailo.com ডোমেন নেই)
        # এটি সরাসরি www.mailo.com ব্যবহার করে, তাই NameResolutionError আসবেই না!
        backup_url = "https://www.mailo.com/mailo/app/api.php"
        backup_payload = {
            "user": EMAIL,
            "pass": MAILO_PASSWORD,
            "action": "send",
            "to": clean_to,
            "subject": f"Re: {clean_subject}",
            "body": body_text
        }
        
        global_memory["reply_status"] = "Attempting Delivery via Mailo Core Gateway..."
        res_backup = requests.post(backup_url, data=backup_payload, timeout=15)
        
        if res_backup.status_code == 200:
            global_memory["reply_status"] = f"✅ SUCCESS! Delivered via Core Gateway to {clean_to}!"
            return True
        else:
            global_memory["reply_status"] = f"⚠️ Mailo Gateway Rejected (Status: {res_backup.status_code})"
            return False

    except Exception as e:
        global_memory["reply_status"] = f"🚨 Gateway Connection Error: {str(e)}"
        return False
