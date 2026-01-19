import os

def fix_max_tokens_recursively(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'max_tokens' in content:
                        print(f"Fixing: {filepath}")
                        new_content = content.replace('max_tokens', 'max_tokens')
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    app_dir = r"c:\Users\PC\Desktop\erasmo\erasmo-backend"
    fix_max_tokens_recursively(app_dir)
    print("Done recursively fixing max_tokens in whole backend.")
