import unittest
from unittest.mock import MagicMock, patch, Mock
from HelloSender import HelloSender
import logging
from vars import SYSTEM_IP, SYSTEM_PORT

class TestHelloSender(unittest.TestCase):
    def setUp(self):
        self.mock_udp_socket = Mock()
        self.registryIP = SYSTEM_IP
        self.registryUDPPort = SYSTEM_PORT
        self.username = "test_user"
        self.udpClientSocket = self.mock_udp_socket
        self.hello_sender = HelloSender(self.username, self.registryIP, self.registryUDPPort, self.udpClientSocket)

    def test_send_message(self):
        # Define the expected message
        expected_message = "HELLO test_user"

        # Call the send_message method
        self.hello_sender.send_message()

        # Check if the sendto method of the UDP socket was called with the expected message
        self.mock_udp_socket.sendto.assert_called_once_with(
            expected_message.encode(), (SYSTEM_IP, SYSTEM_PORT)
        )

    def test_start_timer(self):
        # Start the timer
        self.hello_sender.start_timer()

        # Check if the timer has been started
        self.assertIsNotNone(self.hello_sender.timer)
        self.assertTrue(self.hello_sender.timer.is_alive())

    def tearDown(self):
        # Cancel the timer if it's running to avoid interference with other tests
        if self.hello_sender.timer and self.hello_sender.timer.is_alive():
            self.hello_sender.timer.cancel()

if __name__ == '__main__':
    unittest.main()
