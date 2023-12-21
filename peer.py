'''
    ##  Implementation of peer
    ##  Each peer has a client and a server side that runs on different threads
    ##  150114822 - Eren Ulaş
'''
import os
import sys
from socket import *
import threading
import time
import select
import logging
import ssl
import hashlib
import string
from db import DB
import random
import curses
import re
import pwinput

import db

global chat_log
chat_log = ''
# Server side of peer

class bcolors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    LIGHT_GRAY = '\033[37m'
    DARK_GRAY = '\033[90m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    WHITE = '\033[97m'

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    CONCEAL = '\033[8m'

    ENDC = '\033[0m'


class PeerServer(threading.Thread):
    global chat_log
    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        # keeps the username of the peer
        self.username = username
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        # port number of the peer server
        self.peerServerPort = peerServerPort
        # if 1, then user is already chatting with someone
        # if 0, then user is not chatting with anyone
        self.isChatRequested = 0
        # keeps the socket for the peer that is connected to this peer
        self.connectedPeerSocket = None
        # keeps the ip of the peer that is connected to this peer's server
        self.connectedPeerIP = None
        # keeps the port number of the peer that is connected to this peer's server
        self.connectedPeerPort = None
        # online status of the peer
        self.isOnline = True
        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None

        # TSL connection
        # context = ssl.create_default_context()
        # self.tcpClientSocket = context.wrap_socket(self.tcpClientSocket, server_hostname="192.168.1.7")

    # main method of the peer server thread
    def get_username(self):
        return self.username
    def run(self):

        global chat_log
        print("Peer server started...")

        # gets the ip address of this peer
        # first checks to get it for windows devices
        # if the device that runs this application is not windows
        # it checks to get it for macos devices
        hostname = gethostname()
        try:
            self.peerServerHostname = gethostbyname(hostname)
        except gaierror:
            import netifaces as ni
            self.peerServerHostname = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        # ip address of this peer
        # self.peerServerHostname = 'localhost'
        # socket initializations for the server of the peer
        self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
        self.tcpServerSocket.listen(4)
        # inputs sockets that should be listened
        inputs = [self.tcpServerSocket]
        # server listens as long as there is a socket to listen in the inputs list and the user is online
        while inputs and self.isOnline:
            # monitors for the incoming connections
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                # If a server waits to be connected enters here
                for s in readable:
                    # if the socket that is receiving the connection is 
                    # the tcp socket of the peer's server, enters here
                    if s is self.tcpServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs list
                        # so that we can monitor that socket as well
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                        # if the user is not chatting, then the ip and the socket of
                        # this peer is assigned to server variables
                        if self.isChatRequested == 0:
                            print(self.username + " is connected from " + str(addr))
                            self.connectedPeerSocket = connected
                            self.connectedPeerIP = addr[0]
                    # if the socket that receives the data is the one that
                    # is used to communicate with a connected peer, then enters here
                    else:
                        # message is received from connected peer
                        messageReceived = s.recv(1024).decode()
                        # print("MESSAGE RECEIVED HEREEEEEE " + messageReceived)
                        # logs the received message
                        logging.info("Received from " + str(self.connectedPeerIP) + " -> " + str(messageReceived))
                        # if message is a request message it means that this is the receiver side peer server
                        # so evaluate the chat request
                        if len(messageReceived) > 11 and messageReceived[:12] == "CHAT-REQUEST":
                            # text for proper input choices is printed however OK or REJECT is taken as input in main process of the peer
                            # if the socket that we received the data belongs to the peer that we are chatting with,
                            # enters here
                            if s is self.connectedPeerSocket:
                                # parses the message
                                messageReceived = messageReceived.split()
                                # gets the port of the peer that sends the chat request message
                                self.connectedPeerPort = int(messageReceived[1])
                                # gets the username of the peer sends the chat request message
                                self.chattingClientName = messageReceived[2]
                                # prints prompt for the incoming chat request
                                print("Incoming chat request from " + self.chattingClientName + " >> ")
                                print("Enter OK to accept or REJECT to reject:  ")
                                # makes isChatRequested = 1 which means that peer is chatting with someone
                                self.isChatRequested = 1
                            # if the socket that we received the data does not belong to the peer that we are chatting with
                            # and if the user is already chatting with someone else(isChatRequested = 1), then enters here
                            elif s is not self.connectedPeerSocket and self.isChatRequested == 1:
                                # sends a busy message to the peer that sends a chat request when this peer is 
                                # already chatting with someone else
                                message = "BUSY"
                                s.send(message.encode())
                                # remove the peer from the inputs list so that it will not monitor this socket
                                inputs.remove(s)
                        # if an OK message is received then ischatrequested is made 1 and then next messages will be shown to the peer of this server
                        elif messageReceived == "OK":
                            self.isChatRequested = 1
                        # if an REJECT message is received then ischatrequested is made 0 so that it can receive any other chat requests
                        elif messageReceived == "REJECT":
                            self.isChatRequested = 0
                            inputs.remove(s)
                        # if a message is received, and if this is not a quit message ':q' and 
                        # if it is not an empty message, show this message to the user
                        elif messageReceived[:2] != ":q" and len(messageReceived) != 0:
                            chat_log = chat_log + bcolors.LIGHT_GREEN + self.chattingClientName + bcolors.ENDC + ": " + messageReceived + '\n'
                            os.system('cls')
                            print(chat_log)
                            #print(self.username + ": ", end='')
                            #print(self.chattingClientName + ": " + messageReceived)
                            #print(self.username + ": ")
                        # if the message received is a quit message ':q',
                        # makes ischatrequested 1 to receive new incoming request messages
                        # removes the socket of the connected peer from the inputs list
                        elif messageReceived[:2] == ":q":
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            chat_log = ''
                            # connected peer ended the chat
                            if len(messageReceived) == 2:
                                os.system('cls')
                                print(bcolors.LIGHT_RED + "User you're chatting with ended the chat" + bcolors.ENDC)
                                print(bcolors.LIGHT_RED + "Press enter to quit the chat: " + bcolors.ENDC)
                        # if the message is an empty one, then it means that the
                        # connected user suddenly ended the chat(an error occurred)
                        elif len(messageReceived) == 0:
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            os.system('cls')
                            print(bcolors.LIGHT_RED + "User you're chatting with ended the chat" + bcolors.ENDC)
                            print(bcolors.LIGHT_RED + "Press enter to quit the chat: " + bcolors.ENDC)
                            chat_log = ''
            # handles the exceptions, and logs them
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except ValueError as vErr:
                logging.error("ValueError: {0}".format(vErr))


# Client side of peer
class PeerClient(threading.Thread):
    global chat_log
    # variable initializations for the client side of the peer
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False

        # TSL connection
        # context = ssl.create_default_context()

        # self.tcpClientSocket = context.wrap_socket(self.tcpClientSocket, server_hostname="192.168.1.7")

    def text_manipulation(self, message):  # print("\033[1mThis is bold text.\033[0m")
        edited_message = message[:]

        matches = re.findall(r'(B\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[1m{match[1]}\033[0m")

        matches = re.findall(r'(I\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[3m{match[1]}\033[0m")

        matches = re.findall(r'(U\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[4m{match[1]}\033[0m")

        matches = re.findall(r'(RED\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[93m{match[1]}\033[0m")

        matches = re.findall(r'(GREEN\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[92m{match[1]}\033[0m")

        matches = re.findall(r'(BLUE\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[94m{match[1]}\033[0m")

        return edited_message

    # main method of the peer client thread
    def run(self):
        global chat_log
        print("Peer client started...")
        # connects to the server of other peer
        self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))
        # if the server of this peer is not connected by someone else and if this is the requester side peer client
        # then enters here
        if self.peerServer.isChatRequested == 0 and self.responseReceived is None:
            # composes a request message and this is sent to server and then this waits a response message from the server this client connects
            requestMessage = "CHAT-REQUEST " + str(self.peerServer.peerServerPort) + " " + self.username
            # logs the chat request sent to other peer
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + requestMessage)
            # sends the chat request
            is_disconnected = False
            for i in range(3):
                try:
                    self.tcpClientSocket.send(requestMessage.encode())
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
            #self.tcpClientSocket.send(requestMessage.encode()) ###################################################################
            print("Request message " + requestMessage + " is sent...")
            # received a response from the peer which the request message is sent to
            self.responseReceived = self.tcpClientSocket.recv(1024).decode()
            # logs the received message
            logging.info(
                "Received from " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + self.responseReceived)
            # parses the response for the chat request
            self.responseReceived = self.responseReceived.split()
            # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
            if self.responseReceived[0] == "OK":
                print("Response is " + self.responseReceived[0])
                # changes the status of this client's server to chatting
                self.peerServer.isChatRequested = 1
                # sets the server variable with the username of the peer that this one is chatting
                self.peerServer.chattingClientName = self.responseReceived[1]
                # as long as the server status is chatting, this client can send messages
                #print(self.username + ": ")
                while self.peerServer.isChatRequested == 1:
                    os.system('cls')
                    print(chat_log)
                    # message input prompt
                    messageSent = input('')
                    # messageSent = f'\033[3m{messageSent}\033[0m' ######WORKS
                    messageSent = self.text_manipulation(messageSent)
                    chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + messageSent + '\n'
                    # print(messageSent)
                    # sends the message to the connected peer, and logs it
                    is_disconnected = False
                    for i in range(3):
                        try:
                            self.tcpClientSocket.send(messageSent.encode())
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
                    #self.tcpClientSocket.send(messageSent.encode()) #####################################################
                    #print(self.username + ": ")
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                    # if the quit message is sent, then the server status is changed to not chatting
                    # and this is the side that is ending the chat
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        chat_log = ''
                        os.system('cls')
                        self.isEndingChat = True
                        break
                # if peer is not chatting, checks if this is not the ending side
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        # tries to send a quit message to the connected peer
                        # logs the message and handles the exception
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
                            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                        except BrokenPipeError as bpErr:
                            logging.error("BrokenPipeError: {0}".format(bpErr))
                    # closes the socket
                    chat_log = ''
                    self.responseReceived = None
                    self.tcpClientSocket.close()
            # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
            # logs the message and then the socket is closed       
            elif self.responseReceived[0] == "REJECT":
                print("Response is " + self.responseReceived[0])
                self.peerServer.isChatRequested = 0
                print("client of requester is closing...")
                is_disconnected = False
                for i in range(3):
                    try:
                        self.tcpClientSocket.send("REJECT".encode())
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
                #self.tcpClientSocket.send("REJECT".encode()) ############################################################
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> REJECT")
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print("Receiver peer is busy")
                self.tcpClientSocket.close()
        # if the client is created with OK message it means that this is the client of receiver side peer
        # so it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.
        elif self.responseReceived == "OK":
            # server status is changed
            self.peerServer.isChatRequested = 1
            # ok response is sent to the requester side
            okMessage = "OK"
            is_disconnected = False
            for i in range(3):
                try:
                    self.tcpClientSocket.send(okMessage.encode())
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
            #self.tcpClientSocket.send(okMessage.encode()) #############################################################
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
            print("Client with OK message is created... and sending messages")
            # client can send messsages as long as the server status is chatting
            #print(self.username + ": ")
            while self.peerServer.isChatRequested == 1:
                os.system('cls')
                print(chat_log)
                # input prompt for user to enter message
                messageSent = input('')
                messageSent = self.text_manipulation(messageSent)
                chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + messageSent + '\n'
                is_disconnected = False
                for i in range(3):
                    try:
                        self.tcpClientSocket.send(messageSent.encode())
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
                #self.tcpClientSocket.send(messageSent.encode()) ###################################################
                #print(self.username + ": ")
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    chat_log = ''
                    os.system('cls')
                    break
            # if server is not chatting, and if this is not the ending side
            # sends a quitting message to the server of the other peer
            # then closes the socket
            if self.peerServer.isChatRequested == 0:
                if not self.isEndingChat:
                    is_disconnected = False
                    for i in range(3):
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
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
                    #self.tcpClientSocket.send(":q ending-side".encode()) ###################################################
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                chat_log = ''
                self.responseReceived = None
                self.tcpClientSocket.close()


# main process of the peer
class peerMain:

    # peer initializations
    def __init__(self):
        # ip address of the registry
        os.system('cls')
        while True:
            self.registryName = input("\033[1mEnter IP address of registry: \033[0m")
            if self.registryName == "q":
                print("\033[92mProgram ended successfully.\033[0m")
                exit()
            ip_address_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if not ip_address_pattern.match(self.registryName):
                print("\033[91mInvalid IP address. Try again or enter q to quit.\033[0m")
            else:
                self.registryPort = 15600
                self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                print("\033[96mConnecting, this might take a minute...")
                try:
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                    print("\033[92mConnected Successfully! Loading...\033[0m")
                    time.sleep(3)
                    break
                except:
                    print("\033[91mServer not found or not active. Try again or enter q to quit.\033[0m")
                    #exit()
        # port number of the registry
        #self.registryPort = 15600
        # tcp socket connection to registry
        #print("\033[96mConnecting, this might take a minute...")
        #self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # try:
        #     self.tcpClientSocket.connect((self.registryName, self.registryPort))
        #     print("\033[92mConnected Successfully! Loading...\033[0m")
        #     time.sleep(3)
        # except:
        #     print("\033[91mServer not found or not active. Program ended.\033[0m")
        #     exit()
        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None
        # getting db instance
        self.db = DB()
        choice = "0"
        # TSL connection
        # context = ssl.create_default_context()
        # self.tcpClientSocket = context.wrap_socket(self.tcpClientSocket, server_hostname=self.registryName)

        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            os.system('cls')
            time.sleep(0.2)
            # menu selection prompt
            if not self.isOnline:
                #choice = input("\033[1mChoose an option: \033[0m\n\n\033[3mCreate account: \033[0m1\n\033[3mLogin: \033[0m"
                #              "2\n\033[3mExit: \033[0m3\n")
                print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
                print("1) Create an account\n2) Login\n3) Exit\n")
                choice = input('\033[94m>>> \033[0m')

                while choice not in ['1', '2', '3']:
                    print("\033[91mInvalid choice, try again\033[0m")
                    choice = input('\033[94m>>> \033[0m')
            else:
                #choice = input("\033[1mChoose: \033[0m\n\033[3mLogout: \033[0m1\n\033[3mSearch User: \033[0m2\n"
                #               "\033[3mGet Online Users: \033[0m3\n\033[3mStart a chat: \033[0m"
                #               "4\n")
                print("\033[1m\033[4mChoose an option\033[0m: \033[0m\n")
                print("1) Logout\n2) Search for a user\n3) Show online users\n4) Start a chat\n")
                choice = input('\033[94m>>> \033[0m')

                switch_dict = {
                    "1": "3",
                    "2": "4",
                    "3": "5",
                    "4": "6"
                }
                # Check if the choice is in the dictionary, otherwise set it to the original value
                choice = switch_dict.get(choice, choice)

            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username = input("\033[1mUsername: \033[0m")
                #password = input("\033[1mPassword: \033[0m")
                password = pwinput.pwinput(prompt='\033[1mPassword: \033[0m', mask='*')

                # checks if the password is valid
                while not self.check_password_policy(password):
                    print("If you no longer want to create an account, please enter 'CANCEL'")
                    password = input("\033[1mPassword: \033[0m")
                    if password == "CANCEL":
                        break
                password_hash = self.hash_password(password)
                if password != 'CANCEL':
                    self.createAccount(username, password_hash)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username = input("\033[1mUsername: \033[0m")
                #password = input("\033[1mPassword: \033[0m")
                password = pwinput.pwinput(prompt='\033[1mPassword: \033[0m', mask='*')
                # asks for the port number for server's tcp socket
                #peerServerPort = input("Enter a port number for peer server: ")
                peerServerPort = self.get_random_port()
                # while True:
                #     # each one of the following test has a point.
                #     # port number has to get all three of these point to pass.
                #     counter = 0
                #     # check if port number is a positive number
                #     if self.is_digit(peerServerPort) == False:
                #         print("Port number should be a positive number.")
                #         print(
                #             f"Some of the available port numbers are: {self.get_random_port()} or {self.get_random_port()} or {self.get_random_port()}")
                #         peerServerPort = input("Enter a port number for peer server: ")
                #         continue
                #     else:
                #         counter += 1
                #
                #     peerServerPort = int(peerServerPort)
                #     # check if port number is in private ports range
                #     if peerServerPort < 1024 or peerServerPort > 65535:
                #         print("Port number should be between 1024 and 65535.")
                #         print(
                #             f"Some of the available port numbers are: {self.get_random_port()} or {self.get_random_port()} or {self.get_random_port()}")
                #         peerServerPort = input("Enter a port number for peer server: ")
                #         continue
                #     else:
                #         counter += 1
                #
                #     # check if port number is already in use
                #     if not self.is_port_available(peerServerPort):
                #         print("Port number is already in use. Please choose another one.")
                #         print(
                #             f"Some of the available port numbers are: {self.get_random_port()} or {self.get_random_port()} or {self.get_random_port()}")
                #         peerServerPort = input("Enter a port number for peer server: ")
                #         continue
                #     else:
                #         counter += 1
                #
                #     if counter == 3:
                #         break
                password_hash = self.hash_password(password)
                status = self.login(username, password_hash, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage()
                else:
                    continue
            # if choice is 3 and user is not logged in, then user is informed
            elif choice == "3" and not self.isOnline:
                print("\033[92mProgram ended successfully.\033[0m")
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout()
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient != None:
                    self.peerClient.tcpClientSocket.close()
                print("\033[92mLogged out successfully\033[0m")
                time.sleep(2)
                os.system('cls')

            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched
            elif choice == "4" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username = input("\033[96mUsername to be searched: \033[0m")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print("IP address of " + username + " is " + searchStatus)

            # if choice is 5 and user is online, then user is shown the online users
            elif choice == "5" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                response = self.get_online_users()
                if response[0] == "no-online-users":
                    print("\033[91mNo online users...\033[0m")
                elif response[0] == "get-online-users-success":
                    # list of online users returned includes user who asks for the list, we we remove him from the list
                    online_users = [name for name in response[1:] if name != self.loginCredentials[0]]
                    if len(online_users) == 0:
                        print("\033[91mNo online users...\033[0m")
                    else:
                        print("\033[92mOnline users are: \033[0m" + " ".join(online_users))
                    time.sleep(2)


            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "6" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username = input("\033[96mEnter the username of user to start chat: \033[0m")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]), self.loginCredentials[0],
                                                 self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort,
                                             self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "JOIN " + username + " " + password
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
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
        # self.tcpClientSocket.send(message.encode()) ####################################################
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "join-success":
            print("\033[92mAccount created successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "join-exist":
            print("\033[91mUsername already exists, choose another username. Loading...\033[0m")
            time.sleep(2)

    # password policy check function
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

    # checking if port number is available
    def is_port_available(self, port):
        online_users = self.get_online_users()[1:]  # first element is the response code
        for user in online_users:
            user_port = self.db.get_peer_ip_port(user)[1]
            if int(user_port) == int(port):
                return False
        return True

    # password hashing function
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
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
        # self.tcpClientSocket.send(message.encode()) ###############################################################
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "login-success":
            print("\033[92mLogged in successfully...\033[0m")
            time.sleep(1)
            #os.system('cls')
            return 1
        elif response == "login-account-not-exist":
            print("\033[91mAccount does not exist. Try again\033[0m")
            time.sleep(2)
            #os.system('cls')
            return 0
        elif response == "login-online":
            print("\033[93mAccount is already online.\033[0m")
            time.sleep(2)
            #os.system('cls')
            return 2
        elif response == "login-wrong-password":
            print("\033[91mWrong password. Try again.\033[0m")
            time.sleep(2)
            #os.system('cls')
            return 3

    # logout function
    def logout(self):
        # a logout message is composed and sent to registry
        # timer is stopped
        message = "LOGOUT " + self.loginCredentials[0]
        self.timer.cancel()
        #print(message)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
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
        #self.tcpClientSocket.send(message.encode()) ###################################################################

    # get some random avaliable port numbers
    def get_random_port(self):
        port = 0
        while True:  # can be optimized
            port = random.randint(1024, 65535)
            if self.is_port_available(port):
                break
        return port

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SEARCH " + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
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
        # self.tcpClientSocket.send(message.encode()) ##############################################################
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        if response[0] == "search-success":
            print("\033[92m" + username + " found!\033[0m")
            time.sleep(2)
            return response[1]
        elif response[0] == "search-user-not-online":
            print("\033[93m" + username + " is not online\033[0m")
            time.sleep(2)
            return 0
        elif response[0] == "search-user-not-found":
            print("\033[93m" + username + " is not found\033[0m")
            time.sleep(2)
            return None

    # function for getting online users
    def get_online_users(self):
        message = "GET-ONLINE-USERS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                    dabe = DB()
                    pword = dabe.get_password(self.loginCredentials[0])
                    self.login(self.loginCredentials[0], pword, self.peerServerPort)
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
        # self.tcpClientSocket.send(message.encode()) ##########################################################
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        return response

    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self):
        message = "HELLO " + self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

    # check if port is a number
    def is_digit(self, port):
        try:
            int(port)
            return True
        except ValueError:
            return False


# peer is started
main = peerMain()
