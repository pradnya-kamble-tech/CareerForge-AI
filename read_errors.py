import sys

try:
    with open('tests/pytest_out.txt', 'r', encoding='utf-16le') as f:
        content = f.read()
        if content:
            print("UTF-16LE MATCH!!!\n")
            print(content)
            sys.exit(0)
except Exception:
    pass

try:
    with open('tests/pytest_out.txt', 'r') as f:
        print("NORMAL MATCH!!!\n")
        print(f.read())
except Exception as e:
    print(str(e))
