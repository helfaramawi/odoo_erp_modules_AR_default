import os, re

base = '/mnt/extra-addons'

# Fix all XML files - replace list/tree tags
for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.xml'):
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        new = content
        new = re.sub(r'<list(\s)', r'<tree\1', new)
        new = re.sub(r'<list>', r'<tree>', new)
        new = re.sub(r'</list>', r'</tree>', new)
        new = re.sub(r"view_mode\">([^<]*?)list([^<]*?)</field>",
                     lambda m: 'view_mode">'+m.group(1)+'tree'+m.group(2)+'</field>', new)
        if new != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            print('Fixed XML:', path.replace(base+'/', ''))

# Fix all Python files - remove \n inside string literals
import py_compile
for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(root, fname)
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            print('BAD PY:', path, str(e)[:100])

print('All done. Checking results...')

# Final verification
errors = 0
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('.py'):
            path = os.path.join(root, fname)
            try:
                py_compile.compile(path, doraise=True)
            except:
                errors += 1
                print('STILL BAD:', path)
if errors == 0:
    print('All Python files OK')
