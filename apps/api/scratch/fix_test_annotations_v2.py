import os
import re


def fix_file(filepath) -> None:
    with open(filepath) as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        # Add -> None to test functions
        # Match def test_name(self, args): or def test_name(args):
        # But skip if it already has ->
        if 'def test_' in line and '->' not in line:
            line = re.sub(r'def (test_\w+\(.*\))(\s*):', r'def \1 -> None\2:', line)

        # Add -> None to setup/teardown
        if ('def setup_method' in line or 'def teardown_method' in line) and '->' not in line:
            line = re.sub(r'def (\w+\(.*\))(\s*):', r'def \1 -> None\2:', line)

        # Fix parameters missing annotations in test functions
        # For simple cases like (self, mock_something) -> (self, mock_something: Any)
        if 'def test_' in line:
            # This regex is tricky. Let's try to match (self, arg) or (arg)
            # and replace arg with arg: Any if no colon is present
            parts = re.split(r'(\(|\)|,)', line)
            new_parts = []
            for part in parts:
                p = part.strip()
                if p and p not in ('(', ')', ',', 'self', '') and ':' not in p and not p.startswith('*') and not p.startswith('@'):
                    # It's likely a parameter name
                    # Check if it's followed by -> or : later in the same part (unlikely due to split)
                    new_parts.append(f"{part}: Any")
                else:
                    new_parts.append(part)
            line = "".join(new_parts)

        new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

test_dir = 'tests'
for root, _dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
