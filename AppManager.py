import pwinput
import string
import hashlib
import time
from AccountCreationManager import AccountCreationManager
from RoomManager import RoomManager
from ChatUsersManager import ChatUsersManager


class AppManager:
    def __init__(self):
        self.switch_dict = {
            "1": "3",
            "2": "4",
            "3": "5",
            "4": "6",
            "5": "7",
            "6": "8",
            "7": "9",
            "8": "10",
        }
        self.username = None
        self.accountCreationManager = AccountCreationManager()
        self.roomManager = RoomManager()
        self.chatUsersManager = ChatUsersManager()
        # self.logoutManager = LogOutManager()

    def main_menu_process(self, choice):
        choice = self.switch_dict.get(choice, choice)
        return choice

    def main_menu_page(self):
        print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
        print(
            "1) Logout\n2) Search for a user\n3) Show online users\n4) Start a chat\n5) Create a chat room\n" +
            "6) Join a chat room\n7) Show Available Rooms\n8) Room Chat\n")
        choice = input('\033[94m>>> \033[0m')
        # Check if the choice is in the dictionary, otherwise set it to the original value
        return self.main_menu_process(choice)




    def available_rooms_page(self, username, peerServerPort):
        response = self.roomManager.get_available_rooms(username, peerServerPort)
        if response[0] == "no-available-rooms":
            print("\033[91mNo available rooms...\033[0m")
        elif response[0] == "get-available-rooms-success":
            # list of online users returned includes user who asks for the list, we remove him from the list
            available_rooms = [name for name in response[1:]]
            if len(available_rooms) == 0:
                print("\033[91mNo available rooms...\033[0m")
            else:
                print("\033[92mAvailable rooms are: \033[0m" + " ".join(available_rooms))
        time.sleep(2)

    def start_chat_page(self):
        username_for_chat = input("\033[96mUsername to chat with: \033[0m")
        if username_for_chat == self.username:
            print("\033[91mYou cannot chat with yourself.\033[0m")
            time.sleep(2)
            return None
        return username_for_chat

    def online_users_page(self, username, peerServerPort):
        response = self.chatUsersManager.get_online_users(username, peerServerPort)
        if response[0] == "no-online-users":
            print("\033[91mNo online users...\033[0m")
        elif response[0] == "get-online-users-success":
            # list of online users returned includes user who asks for the list, we remove him from the list
            online_users = [name for name in response[1:] if name != self.username]
            if len(online_users) == 0:
                print("\033[91mNo online users...\033[0m")
            else:
                print("\033[92mOnline users are: \033[0m" + " ".join(online_users))
            time.sleep(2)



    def search_user_page(self):
        username_for_search = input("\033[96mUsername to be searched: \033[0m")
        if username_for_search == self.username:
            print("\033[91mYou cannot search yourself.\033[0m")
            time.sleep(2)
            return None
        return username_for_search

    def start_menu_page(self):
        print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
        print("1) Create an account\n2) Login\n3) Exit\n")
        choice = input('\033[94m>>> \033[0m')

        while choice not in ['1', '2', '3']:
            print("\033[91mInvalid choice, try again\033[0m")
            choice = input('\033[94m>>> \033[0m')
        return choice



    def create_account_page(self):
        username = input("\033[1mUsername: \033[0m")
        password = pwinput.pwinput(prompt='\033[1mPassword: \033[0m', mask='*')

        # checks if the password is valid
        while not self.check_password_policy(password):
            print("If you no longer want to create an account, please enter 'CANCEL'")
            password = input("\033[1mPassword: \033[0m")
            if password == "CANCEL":  # Check with Ramzyyyy
                break
        password_hash = self.hash_password(password)
        self.accountCreationManager.create_account_page(username, password_hash)
        return username, password_hash

    def create_room_page(self, username):
        room_name = input("\033[96mEnter the name of the chat room: \033[0m")
        self.roomManager.create_room(room_name, username)

    def join_room_page(self, username):
        room_name = input("\033[96mEnter the name of the chat room: \033[0m")
        self.roomManager.join_room(room_name, username)

    def check_password_policy(self, password):
        # Password policies
        MIN_PASSWORD_LENGTH = 8
        REQUIRE_DIGIT = True
        REQUIRE_SPECIAL_CHARACTER = True

        # Check minimum length
        if len(password) < MIN_PASSWORD_LENGTH:
            print(f"\033[93mPassword must be at least {MIN_PASSWORD_LENGTH} characters long.\033[0m")
            return False

        # Check digit requirement
        if REQUIRE_DIGIT and not any(char.isdigit() for char in password):
            print("\033[93mPassword must contain at least one digit, one uppercase, and one special character.\033[0m")
            return False

        # Check special character requirement
        if REQUIRE_SPECIAL_CHARACTER and not any(char in string.punctuation for char in password):
            print("\033[93mPassword must contain at least one digit, one uppercase, and one special character.\033[0m")
            return False

        # Check for spaces
        if ' ' in password:
            print("\033[93mPassword must not contain spaces.\033[0m")
            return False
        # All policies passed
        return True

    def login_page(self):
        username = input("\033[1mUsername: \033[0m")
        password = pwinput.pwinput(prompt='\033[1mPassword: \033[0m', mask='*')
        # asks for the port number for server's tcp socket
        password_hash = self.hash_password(password)
        return username, password_hash

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
