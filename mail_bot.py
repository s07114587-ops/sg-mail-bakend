from playwright.sync_api import sync_playwright
import os

def send_hacker_browser_reply(to_email, original_subject):
    global global_memory
    try:
        clean_to = str(to_email).replace('\r', '').replace('\n', '').strip()
        clean_subject = str(original_subject if original_subject else "Mail").replace('\r', '').replace('\n', '').strip()
        body_text = f"Hi!\n\nI successfully received your mail regarding '{clean_subject}'.\n\nBest Regards,\nSubrata Ghosh (SGDEV)"

        # 🚀 ব্যাকগ্রাউন্ডে আসল ক্রোম ব্রাউজার লঞ্চ করা
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) # রেন্ডারে স্ক্রিন ছাড়া চলবে
            page = browser.new_page()
            
            # ১. সরাসরি মেলো লগইন পেজে যাওয়া
            page.goto("https://www.mailo.com/mailo/app/login.php")
            
            # ২. মানুষের মতো টাইপ করে লগইন করা
            page.fill("input[name='login']", EMAIL)
            page.fill("input[name='password']", MAILO_PASSWORD)
            page.click("input[type='submit']") # লগইন বাটনে ক্লিক
            page.wait_for_timeout(3000) # ৩ সেকেন্ড ওয়েট সেশন লোড হতে
            
            # ৩. ডাইরেক্ট মেল কম্পোজ পেজে চলে যাওয়া
            page.goto("https://www.mailo.com/mailo/app/mail.php?page=compose")
            
            # ৪. মেইল ফর্ম ফিলাপ করে সেন্ড করা
            page.fill("input[name='to']", clean_to)
            page.fill("input[name='subject']", f"Re: {clean_subject}")
            page.fill("textarea[name='body']", body_text)
            
            page.click("input[name='submit']") # সেন্ড বাটনে ক্লিক!
            page.wait_for_timeout(2000)
            
            browser.close()
            
        global_memory["reply_status"] = f"✅ HACK SUCCESS! Playwright Browser delivered mail to {clean_to}!"
        return True

except Exception as e:
    global_memory["reply_status"] = f"🚨 Browser Error: {str(e)}"
    return False
