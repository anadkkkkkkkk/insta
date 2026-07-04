import sys, marshal, types, importlib, os, zlib, base64, json, hashlib, subprocess, tempfile
from pathlib import Path

def extract_pyarmor_manual(filepath):
    print(f"[*] جاري فك: {filepath}")
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # البحث عن توقيع Pyarmor (بداية الكود المشفر)
    marker = b'pyarmor_runtime'
    idx = raw.find(marker)
    if idx == -1:
        print("[!] لم يتم العثور على توقيع Pyarmor، الملف غير مشفر؟")
        return
    
    # استخراج القسم المشفر (عادةً بعد import pyarmor_runtime)
    crypto_start = raw.find(b'\x00\x00\x00\x00', idx) + 4
    crypto_data = raw[crypto_start:]
    
    # محاولة فك الضغط باستخدام zlib
    try:
        decomp = zlib.decompress(crypto_data)
        print(f"[+] فك الضغط نجح، الحجم: {len(decomp)}")
        # محاولة تحميل الكود المترجم
        code = marshal.loads(decomp)
        if isinstance(code, types.CodeType):
            print("[+] تم استخراج كود بايثون مترجم بنجاح!")
            # حفظ الكود المترجم
            with open('extracted.pyc', 'wb') as f:
                marshal.dump(code, f)
            # محاولة فك الضغط إلى كود مصدر باستخدام uncompyle6 إن وجد
            try:
                import uncompyle6
                with open('decompiled.py', 'w') as f:
                    uncompyle6.decompile(3.11, code, f)
                print("[+] فك الضغط النهائي نجح -> decompiled.py")
            except ImportError:
                print("[!] uncompyle6 غير مثبت، استخدم الأمر: pip install uncompyle6")
            return code
    except Exception as e:
        print(f"[!] فك الضغط فشل: {e}")
    
    # طريقة بديلة: الاعتراض أثناء التشغيل
    print("[*] محاولة الاعتراض أثناء تشغيل الملف...")
    old_exec = __builtins__.__dict__['exec'] if isinstance(__builtins__, dict) else __builtins__.exec
    
    def intercept_exec(code, *args, **kwargs):
        if isinstance(code, types.CodeType):
            print("[+] تم اعتراض كود مترجم!")
            with open('intercepted.pyc', 'wb') as f:
                marshal.dump(code, f)
            try:
                import uncompyle6
                with open('intercepted_decomp.py', 'w') as f:
                    uncompyle6.decompile(3.11, code, f)
                print("[+] تم فك الكود المعترض -> intercepted_decomp.py")
            except: pass
        return old_exec(code, *args, **kwargs)
    
    if isinstance(__builtins__, dict):
        __builtins__['exec'] = intercept_exec
    else:
        __builtins__.exec = intercept_exec
    
    # تشغيل الملف الأصلي
    with open(filepath, 'r') as f:
        src = f.read()
    try:
        exec(src, {})
    except Exception as e:
        print(f"[*] انتهى التشغيل مع: {e}")
    
    print("[*] اكتمل الاعتراض. تحقق من الملفات المستخرجة.")

if __name__ == '__main__':
    extract_pyarmor_manual('instabrute.py')
