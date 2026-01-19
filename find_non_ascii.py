import os

def find_non_ascii(directory):
    for root, dirs, files in os.walk(directory):
        if ".venv" in dirs:
            dirs.remove(".venv")
        if ".git" in dirs:
            dirs.remove(".git")
        
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        for char in line:
                            if ord(char) > 127:
                                print(f"Non-ASCII in {filepath}:{i+1} -> {char} (U+{ord(char):04X})")
                                break
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    find_non_ascii(r"c:\Users\PC\Desktop\erasmo\erasmo-backend\app")
