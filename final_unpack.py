import marshal, types, sys, dis, zlib, base64, os, importlib, importlib.machinery, importlib.util
from io import BytesIO

# 1. اعتراض `marshal.loads` لتسجيل كل كود يتم تحميله
old_loads = marshal.loads
captured_codes = []

def intercept_loads(data):
    try:
        code = old_loads(data)
        if isinstance(code, types.CodeType):
            captured_codes.append(code)
            print(f"[*] تم اعتراض كود بحجم {len(data)} بايت")
        return code
    except:
        return old_loads(data)

marshal.loads = intercept_loads

# 2. توفير وحدة `pyarmor_runtime` وهمية
class FakeRuntime:
    def __pyarmor__(self, *args, **kwargs):
        return None

sys.modules['pyarmor_runtime_000000'] = FakeRuntime()

# 3. تشغيل الملف المشفر
print("[*] تشغيل الملف المشفر...")
exec(open('instabrute.py', 'rb').read(), {})

# 4. حفظ جميع الأكواد المعترضة
for i, code in enumerate(captured_codes):
    with open(f'code_{i}.pyc', 'wb') as f:
        marshal.dump(code, f)
    print(f"[+] حفظ code_{i}.pyc")

# 5. محاولة فك الكود الأول (عادةً هو الكود الرئيسي)
if captured_codes:
    main_code = captured_codes[0]
    # تفكيكه إلى نص باستخدام uncompyle6
    try:
        import uncompyle6
        with open('final_decompiled.py', 'w', encoding='utf-8') as f:
            uncompyle6.decompile(3.11, main_code, f)
        print("[+] تم فك الكود الرئيسي إلى final_decompiled.py")
    except ImportError:
        print("[!] uncompyle6 غير مثبت – ثبته: pip install uncompyle6")
    # حفظ التفكيك (disassembly) كنسخة احتياطية
    with open('final_disassembly.txt', 'w') as f:
        dis.dis(main_code, file=f)
    print("[+] تم حفظ التفكيك في final_disassembly.txt")
else:
    print("[!] لم يتم اعتراض أي كود")
