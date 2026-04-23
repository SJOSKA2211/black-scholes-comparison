import sys

def wrap_tests(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    in_test = False
    indent = ""
    test_body = []
    
    for line in lines:
        if line.strip().startswith("def test_") and "Any) -> None:" in line:
            # Check if it was originally async (I already changed it to def)
            # Actually, I'll just wrap all test_ that are not already wrapped
            new_lines.append(line)
            new_lines.append("    async def _test():\n")
            in_test = True
            continue
        
        if in_test:
            if line.strip() == "" or line.startswith("@") or line.startswith("def test_"):
                # End of test body
                # Add asyncio.run
                for b_line in test_body:
                    new_lines.append("        " + b_line)
                new_lines.append("    asyncio.run(_test())\n\n")
                test_body = []
                in_test = False
                if line.startswith("def test_"):
                    new_lines.append(line)
                    new_lines.append("    async def _test():\n")
                    in_test = True
                else:
                    new_lines.append(line)
            else:
                test_body.append(line)
        else:
            new_lines.append(line)
            
    if in_test:
        for b_line in test_body:
            new_lines.append("        " + b_line)
        new_lines.append("    asyncio.run(_test())\n")

    with open(filename, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    wrap_tests(sys.argv[1])
