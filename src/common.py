import os
import re
import time

from rich import print as print_rich
from typing import Callable
from rich.markdown import Markdown

from revChatGPT.typings import C

GPT_MODELS = {
    '3.5': 'text-davinci-002-render-sha',
    '4': 'gpt-4',
}

MAX_RETRIES = 5


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


def replace_env_variables(json_string):
    pattern = r"\$\{(\w+)\}"

    def replace(match):
        env_var = match.group(1)
        env_value = os.environ.get(env_var)
        if not env_value:
            raise Exception(f'Environment variable {env_var} not found.')
        env_value = env_value.replace('\\', '/')
        return env_value if env_value else match.group()
    
    updated_json_string = re.sub(pattern, replace, json_string)
    return updated_json_string


def try_chatbot(func: Callable[..., object]) -> Callable[..., object]:
    def wrapper(*args, **kwargs):
        for i in range(0, MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f'{C.FAIL}Error [{i+1}/{MAX_RETRIES}]{C.ENDC}:{e}')
                if i < MAX_RETRIES - 1:
                    print(f'\nRetrying in 3 seconds...\n')
                    time.sleep(3)
        
        time.sleep(0.5)
        print('')
        print(f'{C.BOLD}{C.FAIL}Error: Failed to retry {MAX_RETRIES} times{C.ENDC}')
    
    return wrapper


def print_md(msg, **kwargs):
    msg = msg.replace('You:', f'{C.OKBLUE}You:{C.ENDC}')
    msg = msg.replace('ChatGPT:', f'{C.OKGREEN}ChatGPT:{C.ENDC}')
    print_rich(Markdown(msg), **kwargs)


def get_next_name(name: str):
    if not name:
        return 'user-1'

    dash_index = name.rfind('-')
    if dash_index < 0:
        return f'{name}-1'

    try:
        id = int(name[dash_index + 1:])
        return f'{name[:dash_index]}-{id + 1}'
    except ValueError:
        return f'{name}-1'


def get_next_path_name(path):
    index = path.rfind('.')
    suffix = path[index:]
    prefix = get_next_name(path[:index])

    return prefix + suffix


def get_next_ok_path(path):
    if not os.path.exists(path):
        return path

    return get_next_ok_path(get_next_path_name(path))
