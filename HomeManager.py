import pwinput
import string
import hashlib


class HomeManager:
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

    def start_menu_page(self):
        print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
        print("1) Create an account\n2) Login\n3) Exit\n")
        choice = input('\033[94m>>> \033[0m')

        while choice not in ['1', '2', '3']:
            print("\033[91mInvalid choice, try again\033[0m")
            choice = input('\033[94m>>> \033[0m')
        return choice

    def main_menu_page(self):
        print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
        print(
            "1) Logout\n2) Search for a user\n3) Show online users\n4) Start a chat\n5) Create a chat room\n" +
            "6) Join a chat room\n7) Show Available Rooms\n8) Room Chat\n")
        choice = input('\033[94m>>> \033[0m')

        # Check if the choice is in the dictionary, otherwise set it to the original value
        choice = self.switch_dict.get(choice, choice)
        return choice

    def create_account_page(self):
        username = input("\033[1mUsername: \033[0m")
        password = pwinput.pwinput(prompt='\033[1mPassword: \033[0m', mask='*')

        # checks if the password is valid
        while not self.check_password_policy(password):
            print("If you no longer want to create an account, please enter 'CANCEL'")
            password = input("\033[1mPassword: \033[0m")
            if password == "CANCEL": #Check with Ramzyyyy
                break
        password_hash = self.hash_password(password)
        return username, password_hash

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