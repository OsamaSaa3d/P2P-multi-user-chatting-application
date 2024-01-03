from pymongo import MongoClient


# Includes database operations
class DB:

    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']
        self.online_peers = self.db['online_peers']
        self.rooms = self.db['rooms']
        self.ports = self.db['ports']

    def delete_all_ports(self):
        # Delete all documents in the 'ports' collection
        self.ports.delete_many({})

    def get_room_ports(self, room_name):
        room = self.db.rooms.find_one({'room_name': room_name})
        return room.get('online_participants_ports', [])

    def add_port_to_room(self, room_name, port):
        room = self.db.rooms.find_one({'room_name': room_name})
        ports = room.get('online_participants_ports', [])
        ports.append(port)
        self.db.rooms.update_one(
            {'room_name': room_name},
            {'$set': {'online_participants_ports': ports}}
        )

    def get_all_rooms(self):
        return self.db.rooms.find({})

    def delete_room_online_participants_ports(self, port, room_name):
        room = self.db.rooms.find_one({'room_name': room_name})
        ports = room.get('online_participants_ports', [])
        ports.remove(port)
        self.db.rooms.update_one(
            {'room_name': room_name},
            {'$set': {'online_participants_ports': ports}}
        )



    def clear_online_participants_ports(self):
        self.rooms.update_many({}, {'$set': {'online_participants_ports': []}})
        print("Online participants ports cleared for all rooms.")

    def create_room(self, room_name, username):
        room = {
            'room_name': room_name,
            'participants': [username],  # List to hold participants
            'online_participants_ports': []  # List to hold online participants ports
        }
        self.db.rooms.insert_one(room)

    def create_port(self, port):
        ports = {
            'port': port
        }
        self.db.ports.insert_one(ports)

    def get_all_ports(self):
        return self.db.ports.find({})

    def join_room(self, room_name, username):
        # Find the room by name
        room = self.db.rooms.find_one({'room_name': room_name})

        if room:
            # If room exists, update participants list
            participants = room.get('participants', [])
            if username not in participants:
                participants.append(username)
                # Update the participants field in the room
                self.db.rooms.update_one(
                    {'room_name': room_name},
                    {'$set': {'participants': participants}}
                )

    def delete_room_by_name(self, room_name):
        self.db.rooms.delete_one({'room_name': room_name})
        # Deletes a single room that matches the provided room_name

    def is_room_exist(self, roomname):
        # Use count_documents or estimated_document_count
        count =   self.db.rooms.count_documents({'room_name': roomname})
        if count > 0:
            return True
        return False

    def is_user_in_room(self, username, room_name):
        room = self.db.rooms.find_one({'room_name': room_name})
        if room:
            participants = room.get('participants', [])
            return username in participants
        else:
            return False

    #def get_available_rooms(self):
    #    rooms = self.db.rooms.find({})
    #    return rooms

    def get_room_participants(self, room_name):
        if self.is_room_exist(room_name):
            room = self.db.rooms.find_one({'room_name': room_name})
            return room.get('participants', [])
        else:
            return None

    def add_user_to_room(self, username, room_name):
        room = self.db.rooms.find_one({'room_name': room_name})
        participants = room.get('participants', [])
        participants.append(username)
        self.db.rooms.update_one(
            {'room_name': room_name},
            {'$set': {'participants': participants}}
        )
        return f"User {username} has joined the room {room_name}."

    def delete_all_rooms(self):
        self.db.rooms.delete_many({})
        # Deletes all rooms in the 'rooms' collection

    # checks if an account with the username exists
    def is_account_exist(self, username):
        # Use count_documents or estimated_document_count
        count = self.db.accounts.count_documents({'username': username})
        return count > 0

    # registers a user
    def register(self, username, password):
        account = {'username': username, 'password': password}
        self.db.accounts.insert_one(account)

    # retrieves the password for a given username
    def get_password(self, username):

        user_data = self.db.accounts.find_one({"username": username})
        if user_data:
            return user_data["password"]
        else:
            return None

    # checks if an account with the username online
    def is_account_online(self, username):
        # Use count_documents or estimated_document_count
        count = self.db.online_peers.count_documents({"username": username})
        return count > 0

    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {'username': username, 'ip': ip, 'port': port}
        self.db.online_peers.insert_one(online_peer)

    # logs out the user 
    def user_logout(self, username):
        # Remove the user from the online_peers collection
        self.db.online_peers.delete_one({"username": username})

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        if res:
            return res["ip"], res["port"]
        else:
            return None, None

    # logs out all users in case of a server crash
    # logs out all online users and returns True if any users were logged out, False otherwise
    def logout_all_users(self):
        # Check if there are online users before attempting to log them out
        online_users_count = self.db.online_peers.count_documents({})

        if online_users_count > 0:
            # Delete all documents from the online_peers collection
            self.db.online_peers.delete_many({})
            return True
        else:
            return False
