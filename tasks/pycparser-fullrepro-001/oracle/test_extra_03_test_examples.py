import os
import sys
import unittest
sys.path.insert(0, '.')
from .test_util import run_exe, cpp_supported

class TestExamplesSucceed(unittest.TestCase):

    @unittest.skipUnless(cpp_supported(), 'cpp only works on Unix')
    def test_all_examples(self):
        root = os.path.join(os.path.dirname(__file__), 'examples')
        for filename in os.listdir(root):
            if os.path.splitext(filename)[1] == '.py':
                with self.subTest(name=filename):
                    path = os.path.join(root, filename)
                    (rc, stdout, stderr) = run_exe(path)
                    self.assertEqual(rc, 0, f'example "{filename}" failed with stdout =\n{stdout}\nstderr =\n{stderr}')
if __name__ == '__main__':
    unittest.main()
