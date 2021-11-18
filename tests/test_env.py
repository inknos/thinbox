import os
import shutil
import unittest

from thinbox.config import Env

test_dir = os.path.dirname(__file__)
test_homedir = os.path.join(test_dir, 'home/testuser')

os.environ["HOME"] = test_homedir

os.environ["XDG_CONFIG_HOME"] = os.path.join(test_homedir, ".config")
os.environ["XDG_CACHE_HOME"] = os.path.join(test_homedir, ".XDG_CACHE_HOMEe")


class TestEnv(unittest.TestCase):

    def setUp(self):
        if os.path.exists(test_homedir):
            shutil.rmtree(test_homedir)
        os.makedirs(test_homedir)

        shutil.copyfile(
            os.path.join(test_dir, 'config.test.json'),
            os.path.join(test_homedir, 'config.test.json'))

        self.env = Env()

    def test_defaults(self):
        """Run when no config file is specified
        """
        self.assertEqual(
            self.env.THINBOX_CACHE_DIR,
            os.path.expanduser('~/.cache/thinbox')
        )
        self.assertEqual(
            self.env.THINBOX_BASE_DIR,
            os.path.expanduser('~/.cache/thinbox/base')
        )
        self.assertEqual(
            self.env.THINBOX_IMAGE_DIR,
            os.path.expanduser('~/.cache/thinbox/images')
        )
        self.assertEqual(
            self.env.THINBOX_HASH_DIR,
            os.path.expanduser('~/.cache/thinbox/hash')
        )

    def test_config_file(self):
        self.env = Env(os.path.expanduser('~/config.test.json'))
        self.assertTrue(os.path.exists(
            os.path.expanduser('~/.cache-test')))
        self.assertEqual(
            self.env.THINBOX_CACHE_DIR,
            os.path.expanduser('~/.cache-test/thinbox')
        )
        self.assertEqual(
            self.env.THINBOX_BASE_DIR,
            os.path.expanduser('~/.cache-test/thinbox/base')
        )
        self.assertEqual(
            self.env.THINBOX_IMAGE_DIR,
            os.path.expanduser('~/.cache-test/thinbox/images')
        )
        self.assertEqual(
            self.env.THINBOX_HASH_DIR,
            os.path.expanduser('~/.cache-test/thinbox/hash')
        )

        self.assertEqual(
            self.env.set_key("THINBOX_MEMORY", 2048),
            2048
        )
        self.assertEqual(
            self.env.get_key("THINBOX_MEMORY"),
            2048
        )
        self.assertTrue(os.path.exists(
            os.path.expanduser('~/.config-test/thinbox/config.json')))

    def test_get_key(self):
        self.assertEqual(
            self.env.get_key("THINBOX_CACHE_DIR"),
            os.path.expanduser("~/.cache/thinbox")
        )
        self.assertEqual(
            self.env.THINBOX_CACHE_DIR,
            os.path.expanduser("~/.cache/thinbox")
        )

    def test_set_key(self):
        """Test set_key
        """
        self.assertEqual(
            self.env.set_key("THINBOX_MEMORY", 2048),
            2048
        )
        self.assertEqual(
            self.env.get_key("THINBOX_MEMORY"),
            2048
        )
        self.assertTrue(os.path.exists(
            os.path.expanduser('~/.config/thinbox/config.json')))


    def tearDown(self):
        if os.path.exists(test_homedir):
            shutil.rmtree(test_homedir)

if __name__ == "__main__":
    unittest.main()
