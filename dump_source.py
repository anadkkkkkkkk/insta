import sys, types, importlib, marshal, os

# إنشاء رنتايم مزيف لتجاوز فحص pyarmor
fake = types.ModuleType('pyarmor_runtime_000000')
fake.__pyarmor__ = lambda: None
sys.modules['pyarmor_runtime_000000'] = fake

# تحميل الملف المشفر (سيفك تشفير نفسه تلقائياً)
spec = importlib.util.spec_from_file_location('instabrute', 'instabrute.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# استخراج كل الكائنات البرمجية (Code Objects) من الوحدة
for name, obj in list(mod.__dict__.items()):
    if hasattr(obj, '__code__') and isinstance(obj.__code__, types.CodeType):
        out = f'{name}.pyc'
        with open(out, 'wb') as f:
            marshal.dump(obj.__code__, f)
        print(f'[✔] استخرج: {out}')
    elif hasattr(obj, '__dict__'):
        # استخراج من الكلاسات إذا وجدت
        for sub_name, sub_obj in obj.__dict__.items():
            if hasattr(sub_obj, '__code__'):
                out = f'{name}_{sub_name}.pyc'
                with open(out, 'wb') as f:
                    marshal.dump(sub_obj.__code__, f)
                print(f'[✔] استخرج: {out}')

print('[✔] انتهى الاستخراج')
