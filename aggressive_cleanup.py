import os
import re

# Comprehensive mapping of common emojis/symbols used in the project to ASCII
COMPREHENSIVE_MAP = {
    "[OK]": "[OK]",
    "[ERR]": "[ERR]",
    "[WARN]": "[WARN]",
    "[INIT]": "[INIT]",
    "[SEARCH]": "[SEARCH]",
    "[DELETE]": "[DELETE]",
    "[SAVE]": "[SAVE]",
    "[REFRESH]": "[REFRESH]",
    "[CHAT]": "[CHAT]",
    "[STATS]": "[STATS]",
    "[CLIPBOARD]": "[CLIPBOARD]",
    "[ATTACH]": "[ATTACH]",
    "[USER]": "[USER]",
    "[AI]": "[AI]",
    "[STAR]": "[STAR]",
    "[IDEA]": "[IDEA]",
    "[BUILD]": "[BUILD]",
    "[FOLDER]": "[FOLDER]",
    "[TOKEN]": "[TOKEN]",
    "[DOC]": "[DOC]",
    "[BRAIN]": "[BRAIN]",
    "[KNOWLEDGE]": "[KNOWLEDGE]",
    "[ACTION]": "[ACTION]",
    "[QUERY]": "[QUERY]",
    "[TIME]": "[TIME]",
    "[TIME]": "[TIME]",
    "[Done]": "[Done]",
    "+": "+",
    "+": "+",
    "+": "+",
    "+": "+",
    "+": "+",
    "+": "+",
    "|": "|",
    "-": "-",
    "-": "-",
    "a": "a",
    "e": "e",
    "i": "i",
    "o": "o",
    "u": "u",
    "n": "n",
    "A": "A",
    "E": "E",
    "I": "I",
    "O": "O",
    "U": "U",
    "N": "N",
    "[o]": "[o]",
    "[y]": "[y]",
    "[g]": "[g]"
}

def clean_non_ascii(text):
    for char, replacement in COMPREHENSIVE_MAP.items():
        text = text.replace(char, replacement)
    
    # Final pass for any remaining non-ascii
    result = []
    for char in text:
        if ord(char) > 127:
            # Just remove if not in map
            continue
        result.append(char)
    return "".join(result)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        # We only really care about content in print() or logging calls, 
        # but for simplicity on Windows console, let's clean everything.
        new_content = clean_non_ascii(content)
        
        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Cleaned: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    root_dir = r"c:\Users\PC\Desktop\erasmo\erasmo-backend"
    for root, dirs, files in os.walk(root_dir):
        if ".venv" in dirs:
            dirs.remove(".venv")
        if ".git" in dirs:
            dirs.remove(".git")
            
        for file in files:
            if file.endswith(".py"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
