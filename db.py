from pymongo import MongoClient

# Includes database operations
class DB:


    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']
        self.online_peers = self.db['online_peers']


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
        return self.db.accounts.find_one({"username": username})["password"]


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
        return (res["ip"], res["port"])

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
