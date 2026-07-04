import marshal, types, sys, dis, zlib, base64

def extract_code(filepath):
    print(f"[*] فتح: {filepath}")
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # محاولة استخراج القسم المشفر
    markers = [b'__pyarmor__', b'pyarmor_runtime']
    payload = None
    for m in markers:
        idx = data.find(m)
        if idx != -1:
            # استخراج البيانات بعد العلامة
            offset = idx + len(m) + 4  # تخطي المعرف
            payload = data[offset:]
            break
    
    if payload is None:
        print("[!] لم يتم العثور على بيانات مشفرة")
        return
    
    # محاولة فك التشفير
    for attempt in [lambda x: base64.b64decode(x), lambda x: x]:
        try:
            decoded = attempt(payload)
            decomp = zlib.decompress(decoded)
            code = marshal.loads(decomp)
            if isinstance(code, types.CodeType):
                print("[+] تم استخراج الكود بنجاح!")
                # حفظ الكود المترجم
                with open('extracted_bytecode.pyc', 'wb') as f:
                    marshal.dump(code, f)
                # تفكيك الكود
                with open('disassembly.txt', 'w') as f:
                    dis.dis(code, file=f)
                print("[+] تم حفظ التفكيك في disassembly.txt")
                # محاولة فك الضغط إلى كود نصي باستخدام uncompyle6
                try:
                    import uncompyle6
                    with open('decompiled_source.py', 'w', encoding='utf-8') as f:
                        uncompyle6.decompile(3.11, code, f)
                    print("[+] تم حفظ الكود المصدر المفكوك في decompiled_source.py")
                    # عرض أول 100 سطر
                    with open('decompiled_source.py', 'r') as f:
                        print("\n===== أول 100 سطر من الكود المصدر =====")
                        print(f.read()[:2000])
                except ImportError:
                    print("[!] uncompyle6 غير مثبت. لتثبيته: pip install uncompyle6")
                except Exception as e:
                    print(f"[!] فشل فك الضغط: {e}")
                return
        except Exception as e:
            continue
    
    print("[!] فشل استخراج الكود")

if __name__ == '__main__':
    extract_code('instabrute.py')
