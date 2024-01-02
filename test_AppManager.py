import unittest
from AppManager import *


class TestAppManager(unittest.TestCase):
    def setUp(self):
        self.appManager = AppManager()

    def test_password_length(self):
        self.assertFalse(self.appManager.check_password_policy("short"))  # Test for password too short

    def test_password_digit(self):
        self.assertFalse(self.appManager.check_password_policy("no_digit"))  # Test for no digits in password

    def test_password_special_character(self):
        self.assertFalse(self.appManager.check_password_policy("no_special"))  # Test for no special characters

    def test_password_spaces(self):
        self.assertFalse(self.appManager.check_password_policy("has space"))  # Test for password containing spaces

    def test_valid_password(self):
        self.assertTrue(self.appManager.check_password_policy("GoodPass1!"))  # Test for a valid password
    def test_hash_password(self):
        password = "my_password"
        hashed_password = self.appManager.hash_password(password)

        expected_hash = hashlib.sha256(password.encode()).hexdigest()

        self.assertEqual(hashed_password, expected_hash)


if __name__ == '__main__':
    unittest.main()
