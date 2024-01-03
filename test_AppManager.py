import unittest
from unittest.mock import patch
from AppManager import *


class TestAppManager(unittest.TestCase):
    def setUp(self):
        self.appManager = AppManager()

    @patch('builtins.input', side_effect=['John'])
    @patch('pwinput.pwinput', return_value='password123')
    @patch.object(AppManager, 'hash_password', return_value='hashed_password')
    def test_login_page_valid_input(self, mock_hash_password, mock_pwinput, mock_input):
        result = self.appManager.login_page()
        expected_result = ('John', 'hashed_password')
        self.assertEqual(result, expected_result, "Expected valid input tuple, but got different result")

    @patch('builtins.input', side_effect=['1'])  # Mock user input for testing
    def test_start_menu_page_valid_choice_1(self, mock_input):
        result = self.appManager.start_menu_page()
        self.assertEqual(result, '1', "Expected '1' for choice 1, but got different result")

    @patch('builtins.input', side_effect=['2'])  # Mock user input for testing
    def test_start_menu_page_valid_choice_2(self, mock_input):
        result = self.appManager.start_menu_page()
        self.assertEqual(result, '2', "Expected '2' for choice 2, but got different result")

    @patch('builtins.input', side_effect=['3'])  # Mock user input for testing
    def test_start_menu_page_valid_choice_3(self, mock_input):
        result = self.appManager.start_menu_page()
        self.assertEqual(result, '3', "Expected '3' for choice 3, but got different result")

    @patch('builtins.input', side_effect=['4', '1'])  # Mock user input for testing
    def test_start_menu_page_invalid_then_valid_choice(self, mock_input):
        result = self.appManager.start_menu_page()
        self.assertEqual(result, '1', "Expected '1' after invalid input, but got different result")

    @patch('builtins.input', side_effect=['John'])  # Mock user input for testing
    def test_search_user_page_same_username(self, mock_input):
        self.appManager.username = 'John'  # Set the current user's username
        result = self.appManager.search_user_page()
        self.assertIsNone(result)  # Check if None is returned when same username is entered

    @patch('builtins.input', side_effect=['Jane'])  # Mock user input for testing
    def test_search_user_page_different_username(self, mock_input):
        self.appManager.username = 'John'  # Set the current user's username
        result = self.appManager.search_user_page()
        self.assertEqual(result, 'Jane')  # Check if entered username is returned when different username is entered

    @patch('builtins.input', side_effect=['John'])  # Mock user input for testing
    def test_start_chat_page_same_username(self, mock_input):
        self.appManager.username = 'John'  # Set the current user's username
        result = self.appManager.start_chat_page()
        self.assertIsNone(result)  # Check if None is returned when same username is entered

    @patch('builtins.input', side_effect=['Jane'])  # Mock user input for testing
    def test_start_chat_page_different_username(self, mock_input):
        self.appManager.username = 'John'  # Set the current user's username
        result = self.appManager.start_chat_page()
        self.assertEqual(result, 'Jane')  # Check if entered username is returned when different username is entered

    def test_main_menu_process_valid_choices(self):
        test_cases = [
            ("1", "3"),
            ("2", "4"),
            ("3", "5"),
            ("4", "6"),
            ("5", "7"),
            ("6", "8"),
            ("7", "9"),
            ("8", "10")
        ]

        for choice, expected_result in test_cases:
            with self.subTest(choice=choice, expected_result=expected_result):
                result = self.appManager.main_menu_process(choice)
                self.assertEqual(result, expected_result,
                                 f"Expected {expected_result} for choice {choice}, but got {result}")

    def test_main_menu_process_invalid_choice(self):
        invalid_choice = "invalid_choice"
        result = self.appManager.main_menu_process(invalid_choice)
        self.assertEqual(result, invalid_choice, f"Expected {invalid_choice}, but got {result}")

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
