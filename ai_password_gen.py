#!/usr/bin/env python3
"""
AI Password Generator - الميزة الأسطورية (رقم 5) بتفصيل عالي
يدعم: OpenAI، DeepSeek، ووضع ذكي محلي باستخدام قوالب وتوليفات رياضية
"""

import re
import json
import random
import requests
import argparse
from datetime import datetime

class AIPasswordGenerator:
    def __init__(self, api_key=None, provider="openai", model="gpt-3.5-turbo", base_url=None):
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        
        # إعداد نقاط النهاية
        if provider == "openai":
            self.base_url = base_url or "https://api.openai.com/v1/chat/completions"
            self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        elif provider == "deepseek":
            self.base_url = base_url or "https://api.deepseek.com/v1/chat/completions"
            self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            self.base_url = None
            self.headers = {}
        
        # قاعدة بيانات ذكية للتحويلات (لوكال)
        self.common_suffixes = ["123", "!", "@", "2024", "2025", "2026", "#", "$", "x", "z", "00", "01"]
        self.common_years = [str(y) for y in range(1980, 2027)]
        self.special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "?"]
        self.common_leet = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
    
    def generate_with_ai(self, target_info, count=50, temperature=1.2):
        """
        توليد كلمات مرور باستخدام الذكاء الاصطناعي (API)
        target_info: قاموس يحتوي على (name, birth_year, pet, hobby, city, company)
        """
        if not self.api_key or not self.base_url:
            print("⚠️ لا يوجد مفتاح API، استخدم الوضع المحلي")
            return self.generate_local(target_info, count)
        
        prompt = self._build_smart_prompt(target_info)
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a password cracking expert. Generate realistic, varied passwords based on the given target information. Output ONLY a JSON list of strings."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 2000
            }
            resp = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                text = data['choices'][0]['message']['content']
                # استخراج القائمة من النص
                passwords = self._extract_list(text)
                if passwords:
                    return passwords
        except Exception as e:
            print(f"⚠️ فشل API: {e}")
        
        # الرجوع للوضع المحلي عند الفشل
        return self.generate_local(target_info, count)
    
    def _build_smart_prompt(self, info):
        """بناء موجه ذكي متطور للذكاء الاصطناعي"""
        name = info.get('name', 'user')
        birth_year = info.get('birth_year', '2000')
        pet = info.get('pet', '')
        hobby = info.get('hobby', '')
        city = info.get('city', '')
        company = info.get('company', '')
        
        return f"""
Generate 50 realistic password candidates for a person with the following profile:
- Name: {name} (variations: {name}123, {name}!, {name}2025, etc.)
- Birth Year: {birth_year} (use as suffix)
- Pet Name: {pet} (if exists)
- Hobby: {hobby} (if exists)
- City: {city} (if exists)
- Company: {company} (if exists)

Rules for password generation:
1. Combine base words with numbers, years, and special characters
2. Use common substitutions (a->4, e->3, i->1, o->0, s->5)
3. Generate patterns: [word][year], [word][symbol], [word][year][symbol]
4. Include reversed words and common leetspeak
5. Generate at least 50 unique passwords
6. Output as a JSON list of strings ONLY, no explanations.
Example output: ["John2024!", "j0hn@2025", "petname#2024", ...]
"""
    
    def _extract_list(self, text):
        """استخراج قائمة JSON من رد الذكاء الاصطناعي"""
        try:
            # محاولة تحليل JSON مباشرة
            if text.strip().startswith('['):
                return json.loads(text)
            # محاولة العثور على قائمة داخل النص
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        # استخراج كلمات اعتيادية
        words = re.findall(r'\b\w+\b', text)
        return [w for w in words if len(w) >= 4]
    
    def generate_local(self, target_info, count=50):
        """مولد محلي ذكي جداً (بدون API) باستخدام خوارزميات توليفية"""
        name = target_info.get('name', 'user')
        birth_year = target_info.get('birth_year', '2000')
        pet = target_info.get('pet', '')
        hobby = target_info.get('hobby', '')
        city = target_info.get('city', '')
        
        # قائمة الكلمات الأساسية
        base_words = [name.lower(), name.capitalize(), name.upper()]
        if pet:
            base_words.extend([pet.lower(), pet.capitalize()])
        if hobby:
            base_words.extend([hobby.lower(), hobby.capitalize()])
        if city:
            base_words.extend([city.lower(), city.capitalize()])
        
        # إضافة كلمات عامة قوية
        base_words.extend(["password", "admin", "welcome", "master", "dragon", "freedom", "letmein"])
        
        passwords = set()
        
        # الخوارزميات التوليفية
        for base in base_words:
            if not base or len(base) < 2:
                continue
            
            # 1. إضافة سنوات
            for year in self.common_years:
                passwords.add(f"{base}{year}")
                passwords.add(f"{base}{year}!")
                passwords.add(f"{base}@{year}")
                passwords.add(f"{base}#{year}")
            
            # 2. إضافة رموز خاصة
            for symbol in self.special_chars:
                passwords.add(f"{base}{symbol}")
                passwords.add(f"{base}{symbol}{random.choice(self.common_years)}")
                passwords.add(f"{symbol}{base}")
                passwords.add(f"{symbol}{base}{random.choice(self.common_years)}")
            
            # 3. ليت سبيك (تحويل الحروف لأرقام)
            leet = self._to_leet(base)
            if leet != base:
                passwords.add(leet)
                for year in self.common_years[:10]:
                    passwords.add(f"{leet}{year}")
                    passwords.add(f"{leet}{random.choice(self.special_chars)}{year}")
            
            # 4. عكس الكلمة
            rev = base[::-1]
            passwords.add(rev)
            for year in self.common_years[:10]:
                passwords.add(f"{rev}{year}")
                passwords.add(f"{rev}{random.choice(self.special_chars)}")
            
            # 5. تكرارات
            passwords.add(f"{base}{base}")
            passwords.add(f"{base}{base}{random.choice(self.common_years)}")
            passwords.add(f"{base}{random.choice(self.common_years)}{base}")
            
            # 6. تركيبات شهرية
            months = ["01","02","03","04","05","06","07","08","09","10","11","12"]
            for m in months:
                passwords.add(f"{base}{m}{birth_year}")
                passwords.add(f"{base}.{m}.{birth_year}")
        
        # 7. توليد كلمات عشوائية معقولة
        for _ in range(count * 2):
            w1 = random.choice(base_words) if base_words else "user"
            w2 = random.choice(["123", "2024", "!", "@", "x", "qwerty"])
            w3 = random.choice(self.common_years)
            passwords.add(f"{w1}{w2}{w3}")
            passwords.add(f"{w1}{random.choice(self.special_chars)}{w3}")
            passwords.add(f"{random.choice(self.special_chars)}{w1}{w3}")
        
        # تصفية وتقليم
        passwords = [p for p in passwords if len(p) >= 4 and len(p) <= 20]
        random.shuffle(passwords)
        return passwords[:count * 2]  # ضعف العدد المطلوب للتنوع
    
    def _to_leet(self, word):
        """تحويل النص إلى ليت سبيك"""
        leet = word
        for char, replacement in self.common_leet.items():
            leet = leet.replace(char, replacement)
            leet = leet.replace(char.upper(), replacement.upper())
        return leet

def main():
    parser = argparse.ArgumentParser(description="AI Password Generator - الأسطوري")
    parser.add_argument("--name", default="target", help="اسم الهدف")
    parser.add_argument("--birth-year", default="2000", help="سنة الميلاد")
    parser.add_argument("--pet", default="", help="اسم الحيوان الأليف")
    parser.add_argument("--hobby", default="", help="الهواية")
    parser.add_argument("--city", default="", help="المدينة")
    parser.add_argument("--company", default="", help="الشركة")
    parser.add_argument("--count", type=int, default=100, help="عدد كلمات المرور")
    parser.add_argument("--api-key", help="مفتاح OpenAI أو DeepSeek")
    parser.add_argument("--provider", default="openai", choices=["openai", "deepseek", "local"])
    parser.add_argument("--output", default="ai_passwords.txt")
    parser.add_argument("--format", default="wordlist", choices=["wordlist", "json"])
    
    args = parser.parse_args()
    
    target_info = {
        "name": args.name,
        "birth_year": args.birth_year,
        "pet": args.pet,
        "hobby": args.hobby,
        "city": args.city,
        "company": args.company
    }
    
    gen = AIPasswordGenerator(api_key=args.api_key, provider=args.provider)
    
    print(f"🧠 توليد كلمات مرور للهدف: {args.name}")
    passwords = gen.generate_with_ai(target_info, count=args.count)
    
    # حفظ النتائج
    with open(args.output, 'w') as f:
        if args.format == "json":
            json.dump(passwords, f, indent=2)
        else:
            f.write("\n".join(passwords))
    
    print(f"✅ تم توليد {len(passwords)} كلمة مرور وحفظها في {args.output}")
    
    # عرض عينة
    print("\n🔹 عينة من الكلمات المولدة:")
    for p in passwords[:10]:
        print(f"   - {p}")

if __name__ == "__main__":
    main()
