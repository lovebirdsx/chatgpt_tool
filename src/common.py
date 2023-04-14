import os


def write_file(path: str, content: str) -> None:
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()

def open_file(path: str) -> None:
    os.system(f'explorer {path}')
