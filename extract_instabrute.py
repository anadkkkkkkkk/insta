import sys, types, importlib, marshal, os

# 1. رنتايم وهمي يَقبل أي وسائط
fake = types.ModuleType('pyarmor_runtime_000000')
def fake_pyarmor(name, file, data):
    # هذه الدالة تُستدعى من الملف المشفر، وتعطي الكود المشفر.
    # سنقوم بحفظ البيانات الثنائية لتحليلها لاحقاً.
    with open('pyarmor_data.bin', 'wb') as f:
        f.write(data)
    # نعيد الكائن نفسه (أو أي شيء) لتجنب الأخطاء
    return fake
fake.__pyarmor__ = fake_pyarmor
sys.modules['pyarmor_runtime_000000'] = fake

# 2. تحميل الملف المشفر
spec = importlib.util.spec_from_file_location('__main__', 'instabrute.py')
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception as e:
    print('[!] خطأ أثناء التحميل (متوقع):', e)

# 3. استخراج جميع كائنات Code من الوحدة المحملة
for name, obj in list(mod.__dict__.items()):
    if hasattr(obj, '__code__') and isinstance(obj.__code__, types.CodeType):
        out = f'{name}.pyc'
        with open(out, 'wb') as f:
            marshal.dump(obj.__code__, f)
        print(f'[✔] استخرج: {out}')
    elif isinstance(obj, types.CodeType):
        out = f'{name}_code.pyc'
        with open(out, 'wb') as f:
            marshal.dump(obj, f)
        print(f'[✔] استخرج: {out}')

# 4. البحث في globals() عن كائنات Code أخرى
for name, obj in list(globals().items()):
    if isinstance(obj, types.CodeType):
        out = f'global_{name}.pyc'
        with open(out, 'wb') as f:
            marshal.dump(obj, f)
        print(f'[✔] استخرج: {out}')

print('[✔] انتهى الاستخراج. راجع ملفات .pyc الناتجة.')
