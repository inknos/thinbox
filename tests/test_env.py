import os
import shutil
import unittest

from thinbox.config import Env

test_dir = os.path.dirname(__file__)
test_homedir = os.path.join(test_dir, 'home/testuser')

os.environ["HOME"] = test_homedir
os.environ["XDG_CONFIG_HOME"] = os.path.join(test_homedir, ".config")
os.environ["XDG_CACHE_HOME"] = os.path.join(test_homedir, ".cache")

class TestEnv(unittest.TestCase):

    def setUp(self):
        if os.path.exists(test_homedir):
            shutil.rmtree(test_homedir)
        os.makedirs(test_homedir)

        self.env = Env()

    def test_defaults(self):
        """Run when no config file exists
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
        """Run when config file exists
        """
        shutil.copyfile(
            os.path.join(test_dir, 'config.test.json'),
            os.path.join(test_homedir, '.config/thinbox/config.json'))

        self.env = Env()

        self.test_defaults()

        self.assertEqual(
            self.env.get("THINBOX_MEMORY"),
            2048
        )


    def test_cache_file(self):
        """Run with variables cached
        """
        shutil.copyfile(
            os.path.join(test_dir, 'cache.test.json'),
            os.path.join(test_homedir, '.cache/thinbox/cache.json'))

        self.env = Env()

        self.test_defaults()

        self.assertEqual(
            self.env.get("THINBOX_MEMORY"),
            4096
        )


    def test_config_cache_files(self):
        """Test get variable when config and cache files
        """
        shutil.copyfile(
            os.path.join(test_dir, 'config.test.json'),
            os.path.join(test_homedir, '.config/thinbox/config.json'))

        shutil.copyfile(
            os.path.join(test_dir, 'cache.test.json'),
            os.path.join(test_homedir, '.cache/thinbox/cache.json'))

        self.env = Env()

        self.assertEqual(
            self.env.get("THINBOX_MEMORY"),
            2048
        )


    def test_get_key(self):
        """Test get
        """
        self.test_cache_file()

        self.assertEqual(
            self.env.get("THINBOX_MEMORY"),
            4096
        )


    def test_set_key(self):
        """Test set and create cache file
        """
        self.assertEqual(
            self.env.set("THINBOX_MEMORY", 2048),
            2048
        )
        self.assertEqual(
            self.env.get("THINBOX_MEMORY"),
            2048
        )
        self.assertTrue(os.path.exists(
            os.path.expanduser('~/.cache/thinbox/cache.json')))


    def tearDown(self):
        if os.path.exists(test_homedir):
            shutil.rmtree(test_homedir)

if __name__ == "__main__":
    unittest.main()
