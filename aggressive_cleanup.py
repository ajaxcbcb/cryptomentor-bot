import os
import re

def aggressive_cleanup(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return # Skip binary files

    if '' not in content:
        return

    # Strategy: Keep HEAD (between HEAD and ), remove THEIRS (between  and ajax/main)
    # But for App.jsx we want to merge, so we skip it or handle it.
    
    if filepath.endswith('App.jsx'):
        # App.jsx is already mostly resolved, but if markers remain, handle them.
        pass

    new_content = re.sub(
        r'\n(.*?)\n\n(.*?)\n',
        r'\1',
        content,
        flags=re.DOTALL
    )
    
    # Just in case they are nested or weirdly formatted
    new_content = new_content.replace('', '')
    new_content = new_content.replace('', '')
    new_content = new_content.replace('', '')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Aggressively cleaned {filepath}")

def main():
    root = r'd:\cryptomentorAI'
    for dirpath, _, filenames in os.walk(root):
        if 'node_modules' in dirpath or '.git' in dirpath:
            continue
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ('.py', '.jsx', '.md', '.css', '.txt'):
                aggressive_cleanup(os.path.join(dirpath, filename))

if __name__ == '__main__':
    main()
