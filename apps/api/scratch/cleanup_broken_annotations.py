import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Undo the damage
    # def test_name: Any( -> def test_name(
    new_content = content.replace(': Any(', '(')
    
    if content != new_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

test_dir = 'tests'
for root, dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
