import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        # Replace in dictionary keys and API calls
        content = content.replace('"max_tokens":', '"max_tokens":')
        content = content.replace("'max_tokens':", "'max_tokens':")
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error: {filepath}: {e}")
        return False

# Fix all strategy files
files_to_fix = [
    r"c:\Users\PC\Desktop\erasmo\erasmo-backend\app\services\chat\strategies\advanced_strategy.py",
    r"c:\Users\PC\Desktop\erasmo\erasmo-backend\app\services\chat\strategies\quick_strategy.py",
    r"c:\Users\PC\Desktop\erasmo\erasmo-backend\app\services\conversation_service.py"
]

for filepath in files_to_fix:
    if os.path.exists(filepath):
        replace_in_file(filepath)
    else:
        print(f"Not found: {filepath}")

print("\nDone!")
