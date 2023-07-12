import unittest

from common import get_next_name, get_next_path_name


class TestPath(unittest.TestCase):
    def test_name(self):
        self.assertEqual(get_next_name(''), 'user-1')
        self.assertEqual(get_next_name('hello'), 'hello-1')
        self.assertEqual(get_next_name('hello-1'), 'hello-2')
        self.assertEqual(get_next_name('hello-world'), 'hello-world-1')
    
    def test_get_next_path_name(self):
        self.assertEqual(get_next_path_name('hello.txt'), 'hello-1.txt')
