import unittest
from unittest.mock import patch, MagicMock
from RoomManager import *  # Replace 'your_module' with your actual module name
from unittest.mock import patch
import logging
from vars import SYSTEM_IP, SYSTEM_PORT
from socket import *
class TestRoomManager(unittest.TestCase):

    def setUp(self):
        self.room_manager = RoomManager()

        # Patch 'socket' module for each test case
        self.mock_socket_module = patch('RoomManager.socket').start()
        self.mock_tcp_socket = MagicMock()
        self.mock_socket_module.socket.return_value = self.mock_tcp_socket

    def tearDown(self):
        patch.stopall()  # Stop patching after each test case

    @patch('RoomManager.os')
    def test_create_room_successful(self, mock_os):
        # Mock successful room creation response
        self.mock_tcp_socket.recv.return_value = b'create-room-success'

        # Call the method under test
        result = self.room_manager.create_room('room_name', 'username')

        # Check if the response is as expected
        self.assertEqual(result, 'create-room-success')

    def test_create_room_connection_failure(self):
        # Mock connection failure response
        self.mock_tcp_socket.connect.side_effect = Exception("Connection Error")

        # Call the method under test
        with self.assertRaises(Exception) as cm:
            self.room_manager.create_room('room_name', 'username')

        self.assertEqual(str(cm.exception), "Connection Error")

    def test_create_room_existing(self):
        # Mock room existing response
        self.mock_tcp_socket.recv.return_value = b'create-room-exist'

        # Call the method under test
        result = self.room_manager.create_room('room_name', 'username')

        # Check if the response is as expected
        self.assertEqual(result, 'create-room-exist')


    #@patch('RoomManager.socket')
    #def test_login_successful_connection(self, mock_socket):
    #    mock_tcp_socket = MagicMock()
    #    mock_socket.AF_INET = 'AF_INET'
    #    mock_socket.SOCK_STREAM = 'SOCK_STREAM'
    #    mock_socket.socket.return_value = mock_tcp_socket
#
    #    response = login_request('Welson', 'George@123', 8080)
#
    #    mock_socket.socket.assert_called_once_with(mock_tcp_socket.AF_INET, mock_tcp_socket.SOCK_STREAM)
    #    mock_tcp_socket.connect.assert_called_once_with((SYSTEM_IP, SYSTEM_PORT))
    #    mock_tcp_socket.send.assert_called_once()
    #    self.assertTrue(response)  # Assuming a successful response is True
#
    #@patch('RoomManager.socket')
    #def test_login_connection_timeout(self, mock_socket):
    #    mock_tcp_socket = MagicMock()
    #    mock_socket.socket.return_value = mock_tcp_socket
    #    mock_tcp_socket.connect.side_effect = [TimeoutError] * 10
#
    #    with self.assertRaises(SystemExit) as cm:
    #        login_request('username', 'password', 8080)
#
    #    self.assertEqual(cm.exception.code, 1)
#
    #@patch('RoomManager.socket')
    #def test_login_connection_failure(self, mock_socket):
    #    mock_tcp_socket = MagicMock()
    #    mock_socket.socket.return_value = mock_tcp_socket
    #    mock_tcp_socket.connect.side_effect = Exception("Connection Error")
#
    #    with self.assertRaises(SystemExit) as cm:
    #        login_request('username', 'password', 8080)
#
    #    self.assertEqual(cm.exception.code, 1)



    def test_login_success(self):
        response = "login-success"
        with patch('builtins.print') as mock_print, patch.object(logging, 'info') as mock_info:
            result = login_reaction(response)

            # Check if the correct log message is generated
            mock_info.assert_called_once_with(f"Received from {SYSTEM_IP} -> {response}")

            # Check if the correct message is printed
            mock_print.assert_called_once_with("\033[92mLogged in successfully...\033[0m")

            # Check if the return value is as expected
            self.assertEqual(result, 1)

    def test_login_account_not_exist(self):
        response = "login-account-not-exist"
        with patch('builtins.print') as mock_print, patch.object(logging, 'info') as mock_info:
            result = login_reaction(response)

            mock_info.assert_called_once_with(f"Received from {SYSTEM_IP} -> {response}")
            mock_print.assert_called_once_with("\033[91mAccount does not exist. Try again\033[0m")
            self.assertEqual(result, 0)

    def test_login_online(self):
        response = "login-online"
        with patch('builtins.print') as mock_print, patch.object(logging, 'info') as mock_info:
            result = login_reaction(response)

            mock_info.assert_called_once_with(f"Received from {SYSTEM_IP} -> {response}")
            mock_print.assert_called_once_with("\033[93mAccount is already online.\033[0m")
            self.assertEqual(result, 2)

    def test_login_wrong_password(self):
        response = "login-wrong-password"
        with patch('builtins.print') as mock_print, patch.object(logging, 'info') as mock_info:
            result = login_reaction(response)

            mock_info.assert_called_once_with(f"Received from {SYSTEM_IP} -> {response}")
            mock_print.assert_called_once_with("\033[91mWrong password. Try again.\033[0m")
            self.assertEqual(result, 3)

    def test_join_room_success(self):
        # Mock successful join room response
        self.mock_tcp_socket.recv.return_value = b'join-room-success'

        # Call the method under test
        result = self.room_manager.join_room('room_name', 'username')

        # Check if the response is as expected
        self.assertEqual(result, 'join-room-success')

    def test_join_room_not_exist(self):
        # Mock room does not exist response
        self.mock_tcp_socket.recv.return_value = b'join-room-not-exist'

        # Call the method under test
        result = self.room_manager.join_room('room_name', 'username')

        # Check if the response is as expected
        self.assertEqual(result, 'join-room-not-exist')

    def test_join_room_already_member(self):
        # Mock already a member of the room response
        self.mock_tcp_socket.recv.return_value = b'join-room-already-member'

        # Call the method under test
        result = self.room_manager.join_room('new_Awe', 'Welson')

        # Check if the response is as expected
        self.assertEqual(result, 'join-room-already-member')

    def test_join_room_connection_failure(self):
        # Mock connection failure response
        self.mock_tcp_socket.connect.side_effect = Exception("Connection Error")

        # Call the method under test
        with self.assertRaises(Exception) as cm:
            self.room_manager.join_room('room_name', 'username')

        self.assertEqual(str(cm.exception), "Connection Error")

    @patch('RoomManager.DB')  # Mock the database interaction
    @patch('RoomManager.login')  # Mock the login function
    def test_get_available_rooms_success(self, mock_login, mock_db):
        # Mock successful response from the server
        self.mock_tcp_socket.recv.return_value = b'networj new_geddan new_Awe'

        # Call the method under test
        result = self.room_manager.get_available_rooms('osama', 1234)

        # Check if the response is as expected
        self.assertEqual(result, ['networj', 'new_geddan', 'new_Awe'])

    def test_get_available_rooms_connection_failure(self):
        # Mock connection failure response
        self.mock_tcp_socket.connect.side_effect = Exception("Connection Error")

        # Call the method under test
        with self.assertRaises(Exception) as cm:
            self.room_manager.get_available_rooms('username', 1234)

        self.assertEqual(str(cm.exception), "Connection Error")

    @patch('RoomManager.logging.info')  # Mock the logging.info method
    def test_get_available_rooms_reaction(self, mock_logging):
        # Prepare test data
        response = ['networj', 'new_geddan', 'new_Awe']

        # Call the method under test
        result = self.room_manager.get_available_rooms_reaction(response)

        # Check if the method returns the response as expected
        self.assertEqual(result, response)

        # Check if logging.info was called with the expected arguments
        expected_log = f"Received from {SYSTEM_IP} -> {' '.join(response)}"
        mock_logging.assert_called_once_with(expected_log)



if __name__ == '__main__':
    unittest.main()
