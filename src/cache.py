import os

from app import get_save_path


class Cache:
    def __init__(self, name: str) -> None:
        self.name = name
        self.content = ''

    def read(self, path: str) -> str | None:
        cache_path = self.get_cache_path(path)
        if not os.path.exists(cache_path):
            return None
        
        if not os.path.exists(path):
            return None

        if os.path.getmtime(path) > os.path.getmtime(cache_path):
            return None

        with open(cache_path, 'r') as f:
            return f.read()

    def write(self, path: str, content: str) -> None:
        cache_path = self.get_cache_path(path)
        if not os.path.exists(cache_path):
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        with open(cache_path, 'w') as f:
            f.write(content)

    def get_cache_path(self, path: str) -> str:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        formated_path = path.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.normpath(os.path.join(get_save_path(), 'cache', self.name, f'{formated_path}.md'))

def test_get_cache_path():
    cache = Cache('code_explainer')
    print(cache.get_cache_path('revChatGPT/typings.py'))
    print(cache.get_cache_path('f:\\revChatGPT\\typings.py'))

if __name__ == '__main__':
    test_get_cache_path()