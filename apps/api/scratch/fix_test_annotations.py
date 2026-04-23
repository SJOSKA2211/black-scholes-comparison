import os
import re


def fix_file(filepath) -> None:
    with open(filepath) as f:
        content = f.read()

    # Add -> None to test functions missing return type
    content = re.sub(r'def (test_\w+\(.*\))(\s*):', r'def \1 -> None\2:', content)

    # Add -> None to setup/teardown missing return type
    content = re.sub(r'def (setup_method\(.*\))(\s*):', r'def \1 -> None\2:', content)
    content = re.sub(r'def (teardown_method\(.*\))(\s*):', r'def \1 -> None\2:', content)

    # Note: This is a very basic regex and might miss complex cases or break some.
    # But for standard test files it should work.

    with open(filepath, 'w') as f:
        f.write(content)

test_dir = 'tests'
for root, _dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
