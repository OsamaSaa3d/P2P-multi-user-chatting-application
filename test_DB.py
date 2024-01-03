import unittest
from unittest.mock import MagicMock, patch
from db import DB  # Replace 'your_module' with your actual module


class TestDB(unittest.TestCase):

    def setUp(self):
        self.db_instance = DB()  # Creating an instance of the DB class for testing

        # Mocking MongoClient and database objects
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()

        # Mocking MongoClient and database objects used within DB class
        self.db_instance.client = self.mock_client
        self.db_instance.db = self.mock_db
        self.db_instance.online_peers = self.mock_collection
        self.db_instance.rooms = self.mock_collection
        self.db_instance.ports = self.mock_collection
        self.db_instance.accounts = self.mock_collection

    def tearDown(self):
        # Reset patches
        self.mock_client.reset_mock()
        self.mock_db.reset_mock()
        self.mock_collection.reset_mock()

    def test_delete_all_ports(self):
        # Test delete_all_ports method
        self.db_instance.delete_all_ports()
        self.db_instance.ports.delete_many.assert_called_once()

    def test_get_room_ports(self):
        # Test get_room_ports method
        room_name = "test_room"
        mock_room = {'room_name': room_name, 'online_participants_ports': [8000, 9000]}
        self.db_instance.db.rooms.find_one.return_value = mock_room

        result = self.db_instance.get_room_ports(room_name)
        self.assertEqual(result, [8000, 9000])
        self.db_instance.db.rooms.find_one.assert_called_once_with({'room_name': room_name})

    def test_add_port_to_room(self):
        # Test add_port_to_room method
        room_name = "test_room"
        mock_room = {'room_name': room_name, 'online_participants_ports': [8000]}
        self.db_instance.db.rooms.find_one.return_value = mock_room

        self.db_instance.add_port_to_room(room_name, 9000)
        self.db_instance.db.rooms.update_one.assert_called_once()

    def test_create_room(self):
        # Test create_room method
        room_name = "test_room"
        username = "test_user"
        self.db_instance.create_room(room_name, username)
        self.db_instance.db.rooms.insert_one.assert_called_once()

    def test_create_port(self):
        # Test create_port method
        port = 8000
        self.db_instance.create_port(port)
        self.db_instance.db.ports.insert_one.assert_called_once()

    def test_get_all_rooms(self):
        # Test get_all_rooms method
        mock_rooms = [{'room_name': 'room1'}, {'room_name': 'room2'}]
        self.db_instance.db.rooms.find.return_value = mock_rooms

        result = self.db_instance.get_all_rooms()
        self.assertEqual(result, mock_rooms)
        self.db_instance.db.rooms.find.assert_called_once()

    def test_join_room(self):
        # Test join_room method
        room_name = "test_room"
        username = "test_user"
        mock_room = {'room_name': room_name, 'participants': []}
        self.db_instance.db.rooms.find_one.return_value = mock_room

        self.db_instance.join_room(room_name, username)
        self.db_instance.db.rooms.update_one.assert_called_once()

    def test_delete_room_by_name(self):
        # Test delete_room_by_name method
        room_name = "test_room"
        self.db_instance.delete_room_by_name(room_name)
        self.db_instance.db.rooms.delete_one.assert_called_once()

    def test_is_room_exist(self):
        # Test is_room_exist method
        room_name = "test_room"
        self.db_instance.db.rooms.count_documents.return_value = 1

        result = self.db_instance.is_room_exist(room_name)
        self.assertTrue(result)
        self.db_instance.db.rooms.count_documents.assert_called_once()

    def test_delete_room_online_participants_ports(self):
        # Test delete_room_online_participants_ports method
        room_name = "test_room"
        port = 8000
        mock_room = {'room_name': room_name, 'online_participants_ports': [port]}
        self.db_instance.db.rooms.find_one.return_value = mock_room
        self.db_instance.delete_room_online_participants_ports(port, room_name)
        self.db_instance.db.rooms.update_one.assert_called_once()

    def test_get_all_ports(self):
        # Test get_all_ports method
        mock_ports = [{'port': 8000}, {'port': 9000}]
        self.db_instance.db.ports.find.return_value = mock_ports
        result = self.db_instance.get_all_ports()
        self.assertEqual(result, mock_ports)
        self.db_instance.db.ports.find.assert_called_once()

    def test_delete_all_rooms(self):
        # Test delete_all_rooms method
        self.db_instance.delete_all_rooms()
        self.db_instance.db.rooms.delete_many.assert_called_once()

    def test_logout_all_users_with_online_users(self):
        # Mocking the count_documents and delete_many methods
        with patch.object(self.db_instance.db.online_peers, 'count_documents') as mock_count, \
                patch.object(self.db_instance.db.online_peers, 'delete_many') as mock_delete_many:
            # Simulating online users count > 0
            mock_count.return_value = 2

            result = self.db_instance.logout_all_users()
            mock_count.assert_called_once_with({})
            mock_delete_many.assert_called_once_with({})

            self.assertTrue(result, "Expected True when online users are present")

    def test_logout_all_users_with_no_online_users(self):
        # Mocking the count_documents method
        with patch.object(self.db_instance.db.online_peers, 'count_documents') as mock_count:
            # Simulating online users count = 0
            mock_count.return_value = 0

            result = self.db_instance.logout_all_users()
            mock_count.assert_called_once_with({})
            self.assertFalse(result, "Expected False when no online users are present")

    def test_get_peer_ip_port_existing_user(self):
        username = "test_user"
        mock_result = {"username": username, "ip": "192.168.1.100", "port": 8080}

        # Mocking the find_one method to return a specific result
        with patch.object(self.db_instance.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = mock_result

            ip, port = self.db_instance.get_peer_ip_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(ip, "192.168.1.100")
            self.assertEqual(port, 8080)

    def test_get_peer_ip_port_non_existing_user(self):
        username = "non_existing_user"

        # Mocking the find_one method to return None (user not found)
        with patch.object(self.db_instance.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = None

            ip, port = self.db_instance.get_peer_ip_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertIsNone(ip)
            self.assertIsNone(port)

    def test_user_logout(self):
        username = "test_user"

        # Mocking the delete_one method
        with patch.object(self.db_instance.db.online_peers, 'delete_one') as mock_delete_one:
            self.db_instance.user_logout(username)
            mock_delete_one.assert_called_once_with({"username": username})

    def test_user_login(self):
        username = "test_user"
        ip = "192.168.1.100"
        port = 8080

        # Mocking the insert_one method
        with patch.object(self.db_instance.db.online_peers, 'insert_one') as mock_insert_one:
            self.db_instance.user_login(username, ip, port)
            online_peer = {'username': username, 'ip': ip, 'port': port}
            mock_insert_one.assert_called_once_with(online_peer)

    def test_is_account_online_when_online(self):
        username = "test_user"

        # Mocking the count_documents method
        with patch.object(self.db_instance.db.online_peers, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 1  # Simulating user online

            result = self.db_instance.is_account_online(username)

            mock_count_documents.assert_called_once_with({"username": username})
            self.assertTrue(result, "Expected True when the user is online")

    def test_get_password_existing_user(self):
        username = "existing_user"
        password = "password123"

        # Mocking the find_one method to return a specific result
        with patch.object(self.db_instance.db.accounts, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"username": username, "password": password}

            retrieved_password = self.db_instance.get_password(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(retrieved_password, password)

    def test_get_password_non_existing_user(self):
        username = "non_existing_user"

        # Mocking the find_one method to return None (user not found)
        with patch.object(self.db_instance.db.accounts, 'find_one') as mock_find_one:
            mock_find_one.return_value = None

            retrieved_password = self.db_instance.get_password(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertIsNone(retrieved_password)

    def test_is_account_online_when_offline(self):
        username = "test_user"

        # Mocking the count_documents method
        with patch.object(self.db_instance.db.online_peers, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 0  # Simulating user offline

            result = self.db_instance.is_account_online(username)

            mock_count_documents.assert_called_once_with({"username": username})
            self.assertFalse(result, "Expected False when the user is offline")

    def test_register(self):
        username = "test_user"
        password = "test_password"

        # Mocking the insert_one method
        with patch.object(self.db_instance.db.accounts, 'insert_one') as mock_insert_one:
            self.db_instance.register(username, password)
            account = {'username': username, 'password': password}
            mock_insert_one.assert_called_once_with(account)

    def test_is_account_exist_when_exists(self):
        username = "existing_user"

        # Mocking the count_documents method
        with patch.object(self.db_instance.db.accounts, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 1  # Simulating existing user

            result = self.db_instance.is_account_exist(username)

            mock_count_documents.assert_called_once_with({'username': username})
            self.assertTrue(result, "Expected True for an existing user")

    def test_is_account_exist_when_does_not_exist(self):
        username = "non_existing_user"

        # Mocking the count_documents method
        with patch.object(self.db_instance.db.accounts, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 0  # Simulating non-existing user

            result = self.db_instance.is_account_exist(username)

            mock_count_documents.assert_called_once_with({'username': username})
            self.assertFalse(result, "Expected False for a non-existing user")

    def test_delete_all_rooms(self):
        # Mocking the delete_many method
        with patch.object(self.db_instance.db.rooms, 'delete_many') as mock_delete_many:
            self.db_instance.delete_all_rooms()
            mock_delete_many.assert_called_once_with({})

    def test_add_user_to_room(self):
        username = "test_user"
        room_name = "test_room"

        # Mocking the find_one and update_one methods
        with patch.object(self.db_instance.db.rooms, 'find_one') as mock_find_one, \
                patch.object(self.db_instance.db.rooms, 'update_one') as mock_update_one:
            mock_find_one.return_value = {'room_name': room_name, 'participants': []}

            result = self.db_instance.add_user_to_room(username, room_name)

            mock_find_one.assert_called_once_with({'room_name': room_name})

            expected_participants = [username]
            mock_update_one.assert_called_once_with(
                {'room_name': room_name},
                {'$set': {'participants': expected_participants}}
            )

            self.assertEqual(
                result,
                f"User {username} has joined the room {room_name}.",
                "Expected success message"
            )

    def test_get_room_participants_non_existing_room(self):
        room_name = "non_existing_room"

        # Mocking the is_room_exist method to simulate non-existence of the room
        with patch.object(self.db_instance, 'is_room_exist') as mock_is_room_exist:
            mock_is_room_exist.return_value = False

            result = self.db_instance.get_room_participants(room_name)

            mock_is_room_exist.assert_called_once_with(room_name)
            self.assertIsNone(result, "Expected None for non-existing room")


if __name__ == '__main__':
    unittest.main()
