from bcolors import bcolors
import time
from vars import SYSTEM_IP, SYSTEM_PORT
from socket import *
import logging
import os
class AccountCreationManager:
    def __init__(self, tcpSock=None):
        self.tcpClientSocket = tcpSock

    def create_account_handler(self, username, password_hash):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "JOIN " + username + " " + password_hash
        logging.info("Send to " + SYSTEM_IP + ":" + str(SYSTEM_PORT) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((SYSTEM_IP, SYSTEM_PORT))
                self.tcpClientSocket.send(message.encode())
                break
            except:
                if i == 2:
                    print(bcolors.RED + "Connection to server failed, exiting..." + bcolors.ENDC)
                    is_disconnected = True
                    break
                print(bcolors.RED + "Connection timed out, trying to reconnect..." + bcolors.ENDC)
                time.sleep(2)
        if is_disconnected:
            raise Exception("Connection Error")
            os._exit(1)
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + SYSTEM_IP + " -> " + response)
        if response == "join-success":
            print("\033[92mAccount created successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "join-exist":
            print("\033[91mUsername already exists, choose another username. Loading...\033[0m")
            time.sleep(2)