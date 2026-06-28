<?php
// ভার্সেলের সেটিংস থেকে ডাইরেক্ট সিকিউর পাসওয়ার্ড চলে আসবে!
$password = getenv('MAILO_PASSWORD'); 

if (!$password) {
    die("Error: MAILO_PASSWORD is not set in Vercel Environment Variables!");
}

// Mailo IMAP সেটিংস
$mailbox = "{mail.mailo.com:993/imap/ssl}INBOX";
$username = "sgdev@netc.fr";
$signature = " (it is a automation by Shubhomoy)";

// ইমেইল বক্স ওপেন করা
$inbox = imap_open($mailbox, $username, $password) or die('Cannot connect to Mailo: ' . imap_last_error());
$emails = imap_search($inbox, 'UNSEEN');

if ($emails) {
    foreach ($emails as $mail_id) {
        $overview = imap_fetch_overview($inbox, $mail_id, 0);
        $subject = isset($overview[0]->subject) ? $overview[0]->subject : '';
        $from = $overview[0]->from;
        
        $body = imap_fetchbody($inbox, $mail_id, 1);
        $user_msg = strtolower(trim($body));

        $reply_needed = false;
        $reply_body = "";

        if (strpos($user_msg, "please try my web") !== false) {
            $reply_body = "okay bro I can see it shortly" . $signature;
            $reply_needed = true;
        }
        elseif ($user_msg == "hi" || $user_msg == "hello") {
            $reply_body = "Hello! Welcome to SGDEV Automation System. How can we help you today?" . $signature;
            $reply_needed = true;
        }
        elseif ($user_msg == "how are you") {
            $reply_body = "I am SAI AI, running smoothly and working perfectly! No tension!" . $signature;
            $reply_needed = true;
        }

        if ($reply_needed) {
            $headers = "From: " . $username . "\r\n";
            $headers .= "Reply-To: " . $username . "\r\n";
            $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
            $reply_subject = "Re: " . $subject;
            
            mail($from, $reply_subject, $reply_body, $headers);
            imap_setflag_full($inbox, $mail_id, "\\Seen");
        }
    }
}

imap_close($inbox);
echo "Mail check completed securely via Vercel. No tension!";
?>
