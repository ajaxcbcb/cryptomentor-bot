#!/usr/bin/env python3

# Read the file
with open("Bismillah/menu_handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

print("Applying final Unicode fixes...")

# Fix remaining Unicode issues
content = content.replace('âŒ', '❌')  # cross mark
content = content.replace('ðŸ"„', '🔄')  # refresh
content = content.replace('ðŸ"™', '🔙')  # back arrow
content = content.replace('âœ…', '✅')  # check mark

# Count fixes
print(f"Fixed ❌ symbols: {content.count('❌')}")
print(f"Fixed ✅ symbols: {content.count('✅')}")

# Write back
with open("Bismillah/menu_handlers.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Final Unicode fixes applied!")