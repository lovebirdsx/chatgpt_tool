import os
import re


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
    # 将字符串中的非法字符替换为下划线
    return re.sub(r'[^\w\s-]', '_', s).strip()