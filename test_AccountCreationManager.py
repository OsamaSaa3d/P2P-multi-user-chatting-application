import unittest
from unittest.mock import patch, MagicMock
from AccountCreationManager import AccountCreationManager  # Replace 'your_module' with your actual module name
import logging

class TestCreateAccountPage(unittest.TestCase):
    def setUp(self):
        self.your_instance = AccountCreationManager()  # Create an instance of YourClass

        # Patch 'socket' module for each test case
        self.mock_socket_module = patch('AccountCreationManager.socket').start()
        self.mock_tcp_socket = MagicMock()
        self.mock_socket_module.socket.return_value = self.mock_tcp_socket

    def tearDown(self):
        patch.stopall()  # Stop patching after each test case

    def test_create_account_page_success(self):
        # Mock successful account creation response
        self.mock_tcp_socket.recv.return_value = b'join-success'

        # Call the method under test
        self.your_instance.create_account_page('username', 'password_hash')

        # Check if the appropriate success message is printed
        # You may need to use mock_print or capture the printed output for more complex scenarios

    def test_create_account_page_exist(self):
        # Mock account already exists response
        self.mock_tcp_socket.recv.return_value = b'join-exist'

        # Call the method under test
        self.your_instance.create_account_page('Welson', '')

        # Check if the appropriate exist message is printed
        # You may need to use mock_print or capture the printed output for more complex scenarios

    #def test_create_account_page_connection_failure(self):
    #    # Mock connection failure response
    #    self.mock_tcp_socket.connect.side_effect = Exception("Connection Error")
#
    #    # Call the method under test
    #    with self.assertRaises(Exception) as cm:
    #        self.your_instance.create_account_page('username', '')
#
    #    self.assertEqual(str(cm.exception), "Connection Error")

if __name__ == '__main__':
    unittest.main()
