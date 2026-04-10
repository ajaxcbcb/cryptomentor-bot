import re

def resolve_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Resolving based on "Prefer OURS" but cleanup markers
    content = re.sub(
        r'\n(.*?)\n\n(.*?)\n',
        r'\1',
        content,
        flags=re.DOTALL
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned up {path}")

if __name__ == '__main__':
    paths = [
        r'd:\cryptomentorAI\website-backend\app\routes\dashboard.py',
        r'd:\cryptomentorAI\Bismillah\app\handlers_autotrade.py',
    ]
    for p in paths:
        try:
            resolve_file(p)
        except Exception as e:
            print(f"Failed {p}: {e}")
