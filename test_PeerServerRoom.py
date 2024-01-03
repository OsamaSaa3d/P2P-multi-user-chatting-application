import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from vars import SYSTEM_IP, SYSTEM_PORT
from PeerRoom import PeerServerRoom


class TestPeerServerRoom(unittest.TestCase):
    def test_run_method(self):
        # Mocking necessary components
        udp_socket_mock = MagicMock()
        # Simulate receiving expected data
        udp_socket_mock.recvfrom.return_value = (b"Test message<gL0dDyYi!Z>Hello", ("127.0.0.1", 8080))

        with patch('sys.stdout', new=StringIO()) as fake_output:
            # Create an instance of PeerServerRoom
            peer_server_room = PeerServerRoom(SYSTEM_IP, udp_socket_mock, "test_user", "test_room")
            peer_server_room.run()

            # Asserting the expected output
            expected_output = "Receiving test_room started...\ntest_user: Hello\n"
            self.assertEqual(fake_output.getvalue(), expected_output)


if __name__ == '__main__':
    unittest.main()
