import os
import re

GPT_MODELS = {
    '3.5': 'text-davinci-002-render-sha',
    '4': 'gpt-4',
}

def write_file(path: str, content: str) -> None:
    dir = os.path.dirname(path)
    if dir and not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

    with open(path, 'w') as f:
        f.write(content)


def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def open_file(path: str) -> None:
    os.system(f'explorer {path}')


def to_valid_filename(s):
    return re.sub(r'[^\w\s-]', '_', s).strip()