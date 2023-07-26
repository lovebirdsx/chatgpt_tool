import json
import os

from app import get_save_path

# Example of using Config:
#
# config = Config('config.json')
# config['name'] = 'test'
# config['age'] = 18
# config.save()

class JsonConfig:
    def __init__(self, path):
        self.path = os.path.join(get_save_path(), path)
        self.config = {}
        self.load()
        self.is_dirty = False

    def load(self):
        try:
            with open(self.path, 'r', encoding='utf8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            pass

    def save(self):
        if not self.is_dirty:
            return

        # Create the directory if it does not exist.
        dir_path = os.path.dirname(self.path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(self.path, 'w', encoding='utf8') as file:
            json.dump(self.config, file, indent=2)
        self.is_dirty = False

    def get(self, key):
        if key in self.config:
            return self.config[key]

    def set(self, key, value):
        if self.get(key) != value:
            self.is_dirty = True
        self.config[key] = value

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.config

    def __str__(self):
        return str(self.config)

    def __repr__(self):
        return repr(self.config)
