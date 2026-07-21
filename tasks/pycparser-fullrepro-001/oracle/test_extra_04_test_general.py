import os
import sys
import unittest
sys.path.insert(0, '..')
from pycparser import parse_file, c_ast
from .test_util import cpp_supported, cpp_path, cpp_args

class TestParsing(unittest.TestCase):

    def _find_file(self, name):
        """Find a c file by name, taking into account the current dir can be
        in a couple of typical places
        """
        testdir = os.path.dirname(__file__)
        name = os.path.join(testdir, 'c_files', name)
        assert os.path.exists(name)
        return name

    @unittest.skipUnless(cpp_supported(), 'cpp only works on Unix')
    def test_cpp_funkydir(self):
        if sys.platform != 'win32':
            return
        c_files_path = os.path.join(os.path.dirname(__file__), 'c_files')
        ast = parse_file(self._find_file('simplemain.c'), use_cpp=True, cpp_path=cpp_path(), cpp_args=cpp_args(f'-I{c_files_path}'))
        self.assertIsInstance(ast, c_ast.FileAST)

    @unittest.skipUnless(cpp_supported(), 'cpp only works on Unix')
    def test_c11_with_cpp(self):
        c_files_path = os.path.join(os.path.dirname(__file__), 'c_files')
        fake_libc = os.path.join(c_files_path, '..', 'utils', 'fake_libc_include')
        ast = parse_file(self._find_file('c11.c'), use_cpp=True, cpp_path=cpp_path(), cpp_args=cpp_args(f'-I{fake_libc}'))
        self.assertIsInstance(ast, c_ast.FileAST)
if __name__ == '__main__':
    unittest.main()
