import os
import re

# Emojis used in the project
EMOJI_MAP = {
    "[OK]": "[OK]",
    "[ERR]": "[ERR]",
    "[IMPORTANT]": "[WARN]",
    "[LAUNCH]": "[INIT]",
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
    "[LAUNCH]": "[LAUNCH]",
    "[IDEA]": "[IDEA]",
    "[BUILD]": "[BUILD]",
    "[FOLDER]": "[FOLDER]",
    "[IMPORTANT]": "[IMPORTANT]",
    "[TOKEN]": "[TOKEN]"
}

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for emoji, text in EMOJI_MAP.items():
            content = content.replace(emoji, text)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned: {filepath}")
    except Exception as e:
        print(f"Error cleaning {filepath}: {e}")

def main():
    backend_dir = r"c:\Users\PC\Desktop\erasmo\erasmo-backend"
    for root, dirs, files in os.walk(backend_dir):
        if ".venv" in dirs:
            dirs.remove(".venv")
        if ".git" in dirs:
            dirs.remove(".git")
        
        for file in files:
            if file.endswith(".py"):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
