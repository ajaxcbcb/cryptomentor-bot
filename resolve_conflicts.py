import os
import re

def resolve_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '' not in content:
        return

    # Basic strategy: remove makers and keep both blocks if they look like different functions/components
    # Or keep the one that looks "newer" or "more complete"
    
    # Simple regex to find conflict blocks
    pattern = re.compile(r'\n(.*?)\n\n(.*?)\n', re.DOTALL)
    
    new_content = content
    
    # Specialized resolution for App.jsx
    if filepath.endswith('App.jsx'):
        # Keep both if they are different functions
        def resolver(match):
            ours = match.group(1)
            theirs = match.group(2)
            if 'function RiskManagementCard' in ours and 'function OnboardingWizard' in theirs:
                return ours + '\n\n' + theirs
            if 'const [riskSettings' in ours and 'const [verificationStatus' in theirs:
                 # Prefer a merged list of hooks
                 return ours + '\n' + theirs
            # Default: keep ours (most likely state hooks or main logic)
            return ours
        new_content = pattern.sub(resolver, content)
    
    # Specialized resolution for menu_handlers.py
    elif filepath.endswith('menu_handlers.py'):
        def resolver(match):
            ours = match.group(1)
            theirs = match.group(2)
            # If ours has many handlers and theirs is the redirect list, merge them
            if 'callback_data == MAIN_MENU' in ours and 'callback_data in (' in theirs:
                # This is the main dispatch loop conflict
                # We want to keep the new handlers (account_status, support) and the redirect list
                return theirs 
            return ours
        new_content = pattern.sub(resolver, content)

    else:
        # Default: Prefer HEAD (ours) for most things as we just did a lot of work there
        new_content = pattern.sub(r'\1', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Resolved conflicts in {filepath}")

def main():
    root = r'd:\cryptomentorAI'
    for dirpath, _, filenames in os.walk(root):
        if 'node_modules' in dirpath or '.git' in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(('.jsx', '.py', '.md', '.css')):
                resolve_file(os.path.join(dirpath, filename))

if __name__ == '__main__':
    main()
