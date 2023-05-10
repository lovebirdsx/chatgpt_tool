import os

from common import GPT_MODELS

def get_save_path() -> str:
    home = os.getenv('HOME')
    if not home:
        home = os.getenv('USERPROFILE')
    if not home:
        raise Exception('Unable to access user home directory, please check if the environment variable HOME or USERPROFILE is set.')
    return os.path.normpath(os.path.join(home, '.chatgpt_tool'))


DEFAULT_CONFIG = {
    'proxy': 'socks5h://localhost:38888',
    'model': GPT_MODELS['3.5'],
    'language': 'chinese',
    'access_token': 'open https://chat.openai.com/api/auth/session to get your access_token',
    'export_dir': get_save_path() + '/export',
}


def load_config() -> dict:
    import json
    path = get_save_path() + '/config.json'
    if not os.path.exists(path):
        os.makedirs(get_save_path(), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)
            raise Exception(f'Please configure config.json first, located at: {path}')

    with open(get_save_path() + '/config.json', 'r') as f:
        return json.load(f)


def get_language() -> str:
    return load_config().get('language') or DEFAULT_CONFIG['language']
