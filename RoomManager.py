import logging
from bcolors import bcolors
from socket import *
import os
import time
from vars import SYSTEM_IP, SYSTEM_PORT
from db import DB

def login(username, password, peerServerPort):
    # a login message is composed and sent to registry
    # an integer is returned according to each response
    message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
    logging.info("Send to " + SYSTEM_IP + ":" + str(SYSTEM_IP) + " -> " + message)
    is_disconnected = False
    for i in range(99):
        try:
            if i != 0:
                tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                tcpClientSocket.connect((SYSTEM_IP, SYSTEM_PORT))
            tcpClientSocket.send(message.encode())
            break
        except:
            if i == 89:
                print(bcolors.RED + "Connection to server failed, exiting..." + bcolors.ENDC)
                is_disconnected = True
                break
            print(bcolors.RED + "Connection timed out, trying to reconnect..." + bcolors.ENDC)
            time.sleep(2)
    if is_disconnected:
        os._exit(1)
    response = tcpClientSocket.recv(1024).decode()
    logging.info("Received from " + SYSTEM_IP + " -> " + response)
    if response == "login-success":
        print("\033[92mLogged in successfully...\033[0m")
        time.sleep(2)
        return 1
    elif response == "login-account-not-exist":
        print("\033[91mAccount does not exist. Try again\033[0m")
        time.sleep(2)
        return 0
    elif response == "login-online":
        print("\033[93mAccount is already online.\033[0m")
        time.sleep(2)
        return 2
    elif response == "login-wrong-password":
        print("\033[91mWrong password. Try again.\033[0m")
        time.sleep(2)
        return 3


class RoomManager:

    def __init__(self):
        pass

    def create_room(self, room_name, username):
        message = "CREATE-ROOM" + " " + room_name + " " + username
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
            os._exit(1)
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + SYSTEM_IP + " -> " + response)
        if response == "create-room-success":
            print("\033[92mRoom created successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "create-room-exist":
            print("\033[91mRoom already exists, choose another room name. Loading...\033[0m")
            time.sleep(2)

    def join_room(self, room_name, username):
        message = "JOIN-ROOM" + " " + room_name + " " + username
        logging.info("Send to " + SYSTEM_IP + ":" + SYSTEM_PORT + " -> " + message)
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
            os._exit(1)
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + SYSTEM_IP + " -> " + response)
        if response == "join-room-success":
            print("\033[92mJoined the room successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "join-room-not-exist":
            print("\033[91mRoom does not exist, choose another room name. Loading...\033[0m")
            time.sleep(2)
        elif response == "join-room-already-member":
            print("\033[91mYou are already a member of this room. Loading...\033[0m")
            time.sleep(2)

    def get_available_rooms(self, username, peerServerPort):
        message = "GET-AVAILABLE-ROOMS"
        logging.info("Send to " + SYSTEM_IP + ":" + str(SYSTEM_PORT) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((SYSTEM_IP, SYSTEM_PORT))
                    dabe = DB()
                    pword = dabe.get_password(username)
                    login(username, pword, peerServerPort)
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
            os._exit(1)
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + SYSTEM_IP + " -> " + " ".join(response))
        return response