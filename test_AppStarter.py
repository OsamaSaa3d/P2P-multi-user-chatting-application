import tracemalloc
import unittest
from unittest.mock import patch, MagicMock
from AppStarter import AppStarter
from vars import SYSTEM_IP, SYSTEM_PORT
from socket import *
import sys


class TestAppStarter(unittest.TestCase):

    def setUp(self):
        # Initialize an instance of AppStarter for testing
        self.app_starter = AppStarter()

    def tearDown(self):
        # Clean up any resources if needed
        pass

    def test_get_registryPort(self):
        # Test the get_registryPort method
        self.assertEqual(self.app_starter.get_registryPort(), SYSTEM_PORT)

    def test_initial_tcpClientSocket(self):
        # Test if tcpClientSocket is initially None
        self.assertIsNone(self.app_starter.get_tcpClientSocket())

    @patch('AppStarter.socket')
    def test_establish_connection_success(self, mock_socket_module):
        # Mocking socket.socket() behavior for successful connection
        mock_tcp_socket = MagicMock()
        mock_socket_module.socket.return_value = mock_tcp_socket

        # Call the method under test
        self.app_starter.establish_connection()

        # Check if socket creation and connection were called as expected
        mock_socket_module.socket.assert_called_once_with(mock_socket_module.AF_INET, mock_socket_module.SOCK_STREAM)
        mock_tcp_socket.connect.assert_called_once_with((SYSTEM_IP, SYSTEM_PORT))

    @patch('AppStarter.socket')
    def test_establish_connection_failure(self, mock_socket_module):
        # Mocking socket.socket() behavior for a failed connection
        mock_tcp_socket = MagicMock()
        mock_socket_module.socket.return_value = mock_tcp_socket
        mock_tcp_socket.connect.side_effect = Exception("Connection Error")

        # Call the method under test
        result = self.app_starter.establish_connection()

        # Check if socket creation and connection were called as expected
        mock_socket_module.socket.assert_called_once_with(mock_socket_module.AF_INET, mock_socket_module.SOCK_STREAM)
        mock_tcp_socket.connect.assert_called_once_with((SYSTEM_IP, SYSTEM_PORT))
        self.assertEqual(result, "Connection Error", "Expected failed connection to return 'Connection Error'")

    @patch('builtins.input', side_effect=['valid_ip', 'q'])  # Simulating a valid IP address and 'q' to quit
    @patch.object(AppStarter, 'establish_connection', side_effect=Exception("Server not found or not active"))
    def test_start_app_server_not_found(self, mock_establish_connection, mock_input):
        with patch('builtins.print') as mock_print:
            self.app_starter.start_app()

            # Ensure the error message is printed when the server is not found or not active
            mock_print.assert_called_with(
                "\033[91mServer not found or not active. Try again or enter q to quit.\033[0m")


if __name__ == '__main__':
    # Enable tracemalloc
    tracemalloc.start()
    unittest.main()
