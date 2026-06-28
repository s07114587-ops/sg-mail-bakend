<?php
// ১. ফ্রন্টএন্ড রেপোর সাথে কানেক্ট করার জন্য CORS হেডার (যাতে কোনো এরর না আসে)
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

// তোর সেই স্পেশাল সিগনেচার টেক্সট যা সব অটোমেশনের নিচে দেখাবে
$signature = " (it is a automation by Shubhomoy)";

// ফ্রন্টএন্ড বা ইউআরএল থেকে আসা মেসেজ চেক করা (যেমন: index.php?msg=hi)
$msg = isset($_GET['msg']) ? trim($_GET['msg']) : '';

if (!empty($msg)) {
    // মেসেজটাকে ছোট হাতের অক্ষরে কনভার্ট করা যাতে ক্যাপিটাল লেটার হলেও কাজ করে
    $user_msg = strtolower($msg);
    
    // কন্ডিশন ১: কেউ যদি তার ওয়েবসাইট ট্রাই করতে বলে
    if (strpos($user_msg, "please try my web") !== false) {
        $reply_text = "okay bro I can see it shortly" . $signature;
    }
    // কন্ডিশন ২: সাধারণ Hi বা Hello
    elseif ($user_msg == "hi" || $user_msg == "hello") {
        $reply_text = "Hello! Welcome to SGDEV Automation System. How can we help you today?" . $signature;
    }
    // কন্ডিশন ৩: কেমন আছো জিজ্ঞেস করলে
    elseif ($user_msg == "how are you") {
        $reply_text = "I am SAI AI, running smoothly and working perfectly! No tension!" . $signature;
    }
    // কন্ডিশন ৪: অন্য যেকোনো মেসেজ আসলে ডিফল্ট অটো-রিপ্লাই
    else {
        $reply_text = "Message received! We will send a detailed reply shortly." . $signature;
    }

    // রেসপন্স ডেটা সাজানো
    $reply_data = [
        "bot_reply" => $reply_text,
        "status" => "Automation is live!"
    ];

    // হলুদ স্ক্রিনে আউটপুট পাঠানো
    output_yellow_page($reply_data);
    exit;
}

// কেউ যদি ডাইরেক্ট কোনো মেসেজ ছাড়া মেইন ব্যাকএন্ড লিঙ্কে ঢোকে, তবে তোর সোশ্যাল হাব দেখাবে
$main_data = [
    "status" => "Backend is working, no tension!",
    "message" => "We send reply shortly. You can visit our all social media platforms." . $signature,
    "links" => [
        "main_website" => "https://shubhomoy.dnc.su/",
        "sai_ai" => "https://sai.dnc.su/",
        "dev_to" => "https://dev.to/sgdev_sg_dev",
        "deviantart" => "https://www.deviantart.com/sgdev111",
        "behance" => "https://www.behance.net/sgdev1"
    ]
];

output_yellow_page($main_data);


// 🎨 তোর সেই কাস্টম হলুদ ব্যাকগ্রাউন্ড আর কালো টেক্সট দেখানোর স্পেশাল ফাংশন
function output_yellow_page($data) {
    // JSON ডেটা যাতে সুন্দর ও গোছানো দেখায় তার ব্যবস্থা
    $json_str = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    
    echo '<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SGDEV Backend Automation</title>
    </head>
    <body style="background-color: yellow; font-family: monospace; padding: 20px; margin: 0;">
        <pre style="font-size: 16px; color: black; font-weight: bold; white-space: pre-wrap; word-wrap: break-word;">' . htmlspecialchars($json_str) . '</pre>
    </body>
    </html>';
}
?>
