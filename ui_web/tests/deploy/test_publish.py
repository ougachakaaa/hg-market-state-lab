import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "deploy"))
import publish


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'build'
        self.output.mkdir()
        (self.output / 'index.html').write_text('new')
        self.site = self.root / 'sites' / 'example'
        self.site.mkdir(parents=True)
        (self.site / 'index.html').write_text('old')
        self.config = dict(root=str(self.root), site='sites/example', output='ignored',
                           verify=False, backup=True, retention=2, overwrite=True)
        convert = patch.object(publish.subprocess, 'check_output', return_value=str(self.output))
        convert.start()
        self.addCleanup(convert.stop)

    def test_repeat_keeps_directory_and_creates_no_nested_site(self):
        inode = self.site.stat().st_ino
        publish.main(self.config)
        publish.main(self.config)
        self.assertEqual(self.site.stat().st_ino, inode)
        self.assertEqual((self.site / 'index.html').read_text(), 'new')
        self.assertFalse((self.site / 'build').exists())

    def test_verification_failure_restores_original(self):
        self.config['verify'] = True
        with patch.object(publish, 'verify', side_effect=ValueError('failed')):
            with self.assertRaisesRegex(ValueError, 'failed'):
                publish.main(self.config)
        self.assertEqual((self.site / 'index.html').read_text(), 'old')

    def test_invalid_paths_and_overwrite_rejected(self):
        for path in ('../escape', '/absolute', 'sites/../example'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                publish.main(dict(self.config, site=path))
        (self.root / 'linked').symlink_to(self.site, target_is_directory=True)
        with self.assertRaises(ValueError):
            publish.main(dict(self.config, site='linked'))
        with self.assertRaises(ValueError):
            publish.main(dict(self.config, overwrite=False))
        self.assertEqual((self.site / 'index.html').read_text(), 'old')


if __name__ == '__main__':
    unittest.main()
