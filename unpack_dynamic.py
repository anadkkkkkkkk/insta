import sys, types, importlib, marshal, os, inspect

# 1. إنشاء رنتايم وهمي يحاكي الوحدة المطلوبة
fake_runtime = types.ModuleType('pyarmor_runtime_000000')
def fake_pyarmor(*args, **kwargs):
    # إرجاع كائن يحوي الكود المشفر (يُستخدم لاحقاً)
    return fake_runtime
setattr(fake_runtime, '__pyarmor__', fake_pyarmor)
sys.modules['pyarmor_runtime_000000'] = fake_runtime

# 2. تحميل الملف المشفر
spec = importlib.util.spec_from_file_location('__main__', 'instabrute.py')
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception as e:
    print(f'[!] خطأ في التحميل: {e}')
    # حتى مع الخطأ، قد يكون الكود قد حُقن

# 3. استخراج جميع كائنات Code من الذاكرة
def extract_code_objects(obj, prefix=''):
    if isinstance(obj, types.CodeType):
        out = f'{prefix}code.pyc'
        with open(out, 'wb') as f:
            marshal.dump(obj, f)
        print(f'[✔] استخرج: {out}')
        return
    if hasattr(obj, '__dict__'):
        for name, value in list(obj.__dict__.items()):
            extract_code_objects(value, prefix + name + '_')
    if hasattr(obj, '__code__'):
        extract_code_objects(obj.__code__, prefix + 'func_')
    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            extract_code_objects(item, prefix + f'{i}_')

# 4. البحث في الوحدات المحملة
for name, module in list(sys.modules.items()):
    if name.startswith('pyarmor_'):
        continue
    if hasattr(module, '__dict__'):
        extract_code_objects(module, f'{name}_')

# 5. البحث في الكائنات العامة
extract_code_objects(globals(), 'global_')

# 6. محاولة استخراج __pyarmor__ الموجود في الوحدة الأصلية
if hasattr(mod, '__pyarmor__'):
    code_obj = mod.__pyarmor__
    if isinstance(code_obj, types.CodeType):
        with open('main_code.pyc', 'wb') as f:
            marshal.dump(code_obj, f)
        print('[✔] استخرج main_code.pyc')

print('[✔] انتهى الاستخراج')
