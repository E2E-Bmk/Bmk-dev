import importlib
import unittest

import markdown


def _public_version(version_info):
    major, minor, patch, stage, serial = version_info
    version = f'{major}.{minor}'
    if patch:
        version += f'.{patch}'
    if stage == 'dev':
        version += f'.dev{serial}'
    elif stage != 'final':
        version += {'alpha': 'a', 'beta': 'b', 'rc': 'rc'}[stage] + str(serial)
    return version

class TestVersion(unittest.TestCase):

    def test_get_version(self):
        """Test that public version metadata agrees."""
        self.assertTrue(hasattr(markdown, '__version_info__'))
        version_info = markdown.__version_info__
        self.assertEqual(len(version_info), 5)
        self.assertIn(version_info[3], ('dev', 'alpha', 'beta', 'rc', 'final'))
        self.assertEqual(markdown.__version__, _public_version(version_info))

    def test__version__IsValid(self):
        """Test that __version__ is valid and normalized."""
        try:
            packaging_version = importlib.import_module('packaging.version')
        except ImportError:
            self.skipTest('packaging does not appear to be installed')
        self.assertTrue(hasattr(markdown, '__version__'))
        self.assertEqual(
            markdown.__version__,
            str(packaging_version.Version(markdown.__version__)),
        )
