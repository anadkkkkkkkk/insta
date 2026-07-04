import sys, os, marshal, types, importlib.util, py_compile

def extract_pyarmor(filepath):
    print(f"[*] محاولة فك: {filepath}")
    # محاولة الاستيراد الاعتيادي لالتقاط الكود المترجم
    module_name = os.path.basename(filepath).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    
    # اعتراض دالة exec لاستخراج الكود قبل التنفيذ
    original_exec = __builtins__.__dict__['exec'] if isinstance(__builtins__, dict) else __builtins__.exec
    
    def intercepted_exec(code, *args, **kwargs):
        if isinstance(code, types.CodeType):
            print("[+] تم اعتراض الكود المترجم!")
            # حفظ كـ .pyc
            with open('instabrute_extracted.pyc', 'wb') as f:
                marshal.dump(code, f)
            print("[+] حفظ: instabrute_extracted.pyc")
            try:
                import uncompyle6
                with open('instabrute_decompiled.py', 'w', encoding='utf-8') as f:
                    uncompyle6.decompile(3.11, code, f)
                print("[+] فك الضغط بنجاح -> instabrute_decompiled.py")
            except Exception as e:
                print(f"[!] فشل فك الضغط: {e}")
        return original_exec(code, *args, **kwargs)
    
    if isinstance(__builtins__, dict):
        __builtins__['exec'] = intercepted_exec
    else:
        __builtins__.exec = intercepted_exec
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"[*] تم الاستيراد (الخطأ متوقع): {e}")
    
    # البحث عن أي كود مخزن في ذاكرة الوحدة
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, types.FunctionType):
            code = obj.__code__
            with open(f'func_{attr}.pyc', 'wb') as f:
                marshal.dump(code, f)
            print(f"[+] تم استخراج دالة: {attr}")

if __name__ == '__main__':
    extract_pyarmor('instabrute.py')
