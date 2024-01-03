import unittest
from unittest.mock import patch, MagicMock
from ChatUsersManager import ChatUsersManager  # Replace 'your_module' with your actual module


class TestChatUsersManager(unittest.TestCase):

    def setUp(self):
        self.mock_tcp_socket = MagicMock()
        self.mock_tcp_socket.recv.return_value = "USER1 USER2 USER3"
        self.mock_tcp_socket.connect.return_value = None

        self.mock_socket = patch('ChatUsersManager.socket').start()
        self.mock_socket.return_value = self.mock_tcp_socket

        self.mock_dabe = MagicMock()

        self.mock_login = patch('ChatUsersManager.login').start()
        self.mock_logging = patch('ChatUsersManager.logging').start()
        self.mock_os = patch('ChatUsersManager.os').start()

    def tearDown(self):
        patch.stopall()  # Stop all patches

    def test_get_online_users_success(self):
        self.mock_dabe.get_password.return_value = "password123"
        self.mock_DB = patch('ChatUsersManager.DB').start()
        self.mock_DB.return_value = self.mock_dabe
        # Set up ChatUsersManager instance
        self.chat_manager = ChatUsersManager()

        # Replace these with your actual values
        self.username = "Welson"
        self.peer_server_port = 12345
        # Call the method being tested
        result = self.chat_manager.get_online_users(self.username, self.peer_server_port)

        # Assertions
        self.assertEqual(result, ["USER1", "USER2", "USER3"])
        self.mock_logging.info.assert_called()
        self.mock_tcp_socket.connect.assert_called_once()
        self.mock_dabe.get_password.assert_called_once_with(self.username)
        self.mock_login.assert_called_once_with(self.username, "password123", self.peer_server_port)
        self.mock_tcp_socket.send.assert_called_once()
        self.mock_tcp_socket.recv.assert_called_once()

    # Add more test cases for failure scenarios, exceptions, etc. if necessary


if __name__ == '__main__':
    unittest.main()
