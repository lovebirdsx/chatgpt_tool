import os


def get_save_path() -> str:
    home = os.getenv('HOME')
    if not home:
        home = os.getenv('USERPROFILE')
    if not home:
        raise Exception('无法获取用户主目录, 请检查环境变量是否设置HOME或USERPROFILE')
    return os.path.normpath(os.path.join(home, '.chatgpt_tools'))
