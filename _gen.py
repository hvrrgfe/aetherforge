import os

base = r'D:\game\AetherForgeStudio\src\com\aetherforge'

def write(path, code):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(os.path.basename(path) + ': ' + str(code.count(chr(10))) + ' lines')
print(" Starting LayoutBuilder...\)\n