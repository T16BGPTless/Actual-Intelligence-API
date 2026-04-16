with open("tests/conftest.py", "r") as f:
    c = f.read()

if "def limit(" not in c:
    c = c.replace('def maybe_single(', 'def limit(self, *_args, **_kwargs):\n        return self\n\n    def maybe_single(')

with open("tests/conftest.py", "w") as f:
    f.write(c)
