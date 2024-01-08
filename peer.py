from bcolors import bcolors
from vars import SYSTEM_IP, SYSTEM_PORT, chat_log
from TextManipulator import TextManipulator
from HelloSender import HelloSender
from AppStarter import AppStarter
from AppManager import AppManager
from PeerRoom import PeerServerRoom, PeerClientRoom
import os
from socket import *
import threading
import time
import logging
import select
from db import DB
import random
# Server side of peer


global registryIP
registryIP = SYSTEM_IP
global registryPort
registryPort = SYSTEM_PORT


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
                                # print("Incoming chat request from " + self.chattingClientName + " >> ")
                                # print("Enter OK to accept, REJECT to reject : ")
                                print(
                                    bcolors.LIGHT_CYAN + self.chattingClientName + " has sent you a chat request!" + bcolors.ENDC)
                                print(
                                    bcolors.LIGHT_CYAN + "Enter OK to accept, or REJECT to reject the chat request: " + bcolors.ENDC)
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
        # client side tcp socket initialization
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False
        self.udpPortRoom = None
        self.text_manipulator = TextManipulator()

        # TSL connection
        # context = ssl.create_default_context()

        # self.tcpClientSocket = context.wrap_socket(self.tcpClientSocket, server_hostname="192.168.1.7")

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
                    if i != 0:
                        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                        self.tcpClientSocket.connect((registryIP, registryPort))
                        dabe = DB()
                        pword = dabe.get_password(self.username)
                        login(self.username, pword, self.peerServer.peerServerPort)
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
                # print(self.username + ": ")
                while self.peerServer.isChatRequested == 1:
                    os.system('cls')
                    print(chat_log)
                    # message input prompt
                    messageSent = input('')
                    messageSent = self.text_manipulator.manipulate(messageSent)
                    chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + messageSent + '\n'
                    # sends the message to the connected peer, and logs it
                    is_disconnected = False

                    try:
                        self.tcpClientSocket.send(messageSent.encode())
                    except:
                        print(bcolors.RED + "Lost connection to user, exiting..." + bcolors.ENDC)
                        is_disconnected = True
                        time.sleep(2)

                    if is_disconnected:
                        break
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
                # print("Response is " + self.responseReceived[0])
                self.peerServer.isChatRequested = 0
                print(bcolors.RED + "User has rejected the chat request. Redirecting to main menu..." + bcolors.ENDC)
                time.sleep(2)
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
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> REJECT")
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print(
                    bcolors.RED + "User is currently busy, try again another time. Redirecting to main menu..." + bcolors.ENDC)
                time.sleep(3)
                self.tcpClientSocket.close()
            elif self.responseReceived[0] != "BUSY":
                print(
                    bcolors.RED + "User is currently busy, try again another time. Redirecting to main menu..." + bcolors.ENDC)
                time.sleep(3)
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
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
            print("Client with OK message is created... and sending messages")
            # client can send messsages as long as the server status is chatting
            # print(self.username + ": ")
            while self.peerServer.isChatRequested == 1:
                os.system('cls')
                print(chat_log)
                # input prompt for user to enter message
                messageSent = input('')
                messageSent = self.text_manipulator.manipulate(messageSent)
                chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + messageSent + '\n'
                is_disconnected = False
                try:
                    self.tcpClientSocket.send(messageSent.encode())
                except:
                    print(bcolors.RED + "Lost connection to user, exiting..." + bcolors.ENDC)
                    is_disconnected = True
                    time.sleep(2)

                if is_disconnected:
                    break

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
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                chat_log = ''
                self.responseReceived = None
                self.tcpClientSocket.close()


# main process of the peer
class peerMain:
    # peer initializations
    def __init__(self):
        global registryIP
        # ip address of the registry
        os.system('cls')

        with open('performance_test.txt', 'w') as file:
            # Write lines to the file
            file.write("This is a performance test for all the functionalities in the peer-to-peer chat application.\n")
            file.write("Under the supervision and guidance of Professor Ayman Bahaa\n")
            file.write("By: George Welson\n")
            file.write("    Kareem Ramzy\n")
            file.write("    Osama Saad\n")
            file.write("    Youssef Barakat\n")
            file.write("\n")
            file.write("\n")
            file.write("The following are the results of the performance test:\n")
            file.write("A peer has started")


        self.registryName = registryIP
        self.app_starter = AppStarter()
        before = time.time()
        self.app_starter.start_app()
        after = time.time()
        elapsed_time = after - before
        with open('performance_test.txt', 'a') as file:
            file.write("A peer has detected a registry and connected with it using a tcp connection in "+ str(round(elapsed_time,3)) + " seconds\n")
        self.tcpClientSocket = self.app_starter.get_tcpClientSocket()
        self.registryPort = self.app_starter.get_registryPort()

        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.username = None
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
        self.helloSender = None
        self.appManager = AppManager(self.tcpClientSocket)
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
                before = time.time()
                choice = self.appManager.start_menu_page()
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the start menu and prompted the user to create account, login or "
                               + "exit the app in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")

            else:
                before = time.time()
                choice = self.appManager.main_menu_page()
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the main menu, set the user status to online and prompted the user "
                               + "to search for a user, see online users, "
                               + "start a chat, create a room, join a room, see available rooms, wait for other users "
                               + "to initiate a chat or logout in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")

            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                self.appManager.create_account_page()
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the create account menu and prompted the user to enter a username "
                               + "and password in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
                #username, password_hash = self.appManager.create_account_page()
                # if password != 'CANCEL':
                #self.createAccount(username, password_hash)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                username, password_hash = self.appManager.login_page()
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the login menu and prompted the user to enter a username "
                               + "and password in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
                # peerServerPort = self.get_random_port()
                peerServerPort = self.get_available_port_new()
                status = self.login(username, password_hash, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.username = username
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(username, self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.helloSender = HelloSender(username, self.registryName, self.registryUDPPort,
                                                   self.udpClientSocket)
                    self.helloSender.sendHelloMessage()
                else:
                    continue
            # if choice is 3 and user is not logged in, then user is informed
            elif choice == "3":
                if not self.isOnline:
                    print("\033[92mProgram ended successfully.\033[0m")
                # if choice is 3 and user is logged in, then user is logged out
                # and peer variables are set, and server and client sockets are closed
                else:
                    before = time.time()
                    self.logout()
                    after = time.time()
                    elapsed_time = after - before
                    with open('performance_test.txt', 'a') as file:
                        file.write("The app has logged out the user in :" + str(round(elapsed_time,3)) + " seconds\n")
                    self.isOnline = False
                    self.username = None
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
                before = time.time()
                username_for_search = self.appManager.search_user_page()
                searchStatus = self.searchUser(username_for_search)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the search user menu and prompted the user to enter a username "
                               + "in :" + str(round(elapsed_time, 3)) + " seconds\n")
                    file.write("This process depends on user input\n")
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print("IP address of " + username_for_search + " is " + searchStatus)
                else:
                    print(f"\033[91mCannot chat with {username_for_search} ...\033[0m")

            # if choice is 5 and user is online, then user is shown the online users
            elif choice == "5" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                self.appManager.online_users_page(self.username, self.peerServerPort)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has checked the database for currently online peers and showed them to the user"
                               + " in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process does not depend on user input\n")

            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "6" and self.isOnline:
                os.system('cls')
                before = time.time()
                time.sleep(0.2)
                username_for_chat = self.appManager.start_chat_page()
                searchStatus = self.searchUser(username_for_chat)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the start chat menu, prompted the user to enter a username and "
                               "opened a chat " + "in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
                print(searchStatus)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]), self.username,
                                                 self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "7" and self.isOnline:
                os.system('cls')
                before = time.time()
                time.sleep(0.2)
                self.appManager.create_room_page(self.username)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the create room page, prompted the user to enter a room name and "
                               "created a room " + "in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
            elif choice == "8" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                self.appManager.join_room_page(self.username)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the join room page, prompted the user to enter a room name and "
                               "joined a room " + "in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
            elif choice == "9" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                self.appManager.available_rooms_page(self.username, self.peerServerPort)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has checked the database for currently available rooms and showed them to the "
                               + "user in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process does not depend on user input\n")
            elif choice == "10" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                before = time.time()
                room_name = input("\033[96mEnter the name of the room: \033[0m")
                udpPort = self.get_available_port_new()
                db = DB()
                participants = db.get_room_participants(room_name)
                if participants:
                    if self.username not in participants:
                        print("\033[91mYou're not registered in the room...\033[0m")
                        time.sleep(2)
                        continue
                else:
                    print("\033[91mRoom does not exist...\033[0m")
                    time.sleep(2)
                    continue
                response = self.get_room_peers(room_name)
                self.add_port_to_room(room_name, udpPort)

                self.udpClientSocket_room = socket(AF_INET, SOCK_DGRAM)

                self.udpClientSocket_room.bind((registryIP, udpPort))
                self.serverRoom = PeerServerRoom(registryIP, self.udpClientSocket_room, self.username, room_name)
                self.serverRoom.start()
                # self.serverRoom.join()
                self.udpRoom = PeerClientRoom(registryIP, self.udpClientSocket_room, udpPort, response,
                                              self.username, self.peerServer, room_name)
                after = time.time()
                elapsed_time = after - before
                with open('performance_test.txt', 'a') as file:
                    file.write("The app has launched the chat room page, prompted the user to enter a message " +
                               " or wait to receive a message in :" + str(round(elapsed_time,3)) + " seconds\n")
                    file.write("This process depends on user input\n")
                self.udpRoom.start()
                self.udpRoom.join()



            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.username
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort,
                                             self.username, self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.helloSender.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()



    def add_port_to_room(self, room_name, port):
        message = "ROOM-PEERS-ADD" + " " + room_name + " " + str(port)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
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
        print(response)

    def get_room_peers(self, room_name):
        message = "ROOM-PEERS" + " " + room_name
        logging.info("Get room users in " + room_name)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
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
        # Split the string by spaces
        port_list = response.split()

        # Remove the first element since it's not a number
        port_list = port_list[1:]

        # Convert strings to integers
        port_list = [int(num) for num in port_list]
        print(port_list)
        time.sleep(1)
        return response




    def get_available_port_new(self):
        port = 0
        while True:
            port = random.randint(1024, 65535)
            if self.is_port_available_new(port):
                break
        self.db.create_port(port)
        return port

    def is_port_available_new(self, port):
        taken_ports = self.db.get_all_ports()
        for p in taken_ports:
            if int(p['port']) == int(port) or int(port) == 15500 or int(port) == 15600:
                return False
        return True


    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(99):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                self.tcpClientSocket.send(message.encode())
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
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
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

    # logout function
    def logout(self):
        # a logout message is composed and sent to registry
        # timer is stopped
        message = "LOGOUT " + self.username
        self.helloSender.timer.cancel()
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                    dabe = DB()
                    pword = dabe.get_password(self.username)
                    self.login(self.username, pword, self.peerServerPort)
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



    def search_user_in_room(self, room_name, username):
        message = "SEARCH-ROOM-USERS" + " " + room_name + " " + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        is_disconnected = False
        for i in range(3):
            try:
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                    dabe = DB()
                    pword = dabe.get_password(self.username)
                    self.login(self.username, pword, self.peerServerPort)
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
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "search-user-room-success":
            print("\033[92mRoom found successfully! Loading...\033[0m")
            time.sleep(2)
            return response[1]
        elif response == "search-room-not-available":
            print("\033[91mRoom not available. Loading...\033[0m")
            time.sleep(2)
            return None

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
                if i != 0:
                    self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    self.tcpClientSocket.connect((self.registryName, self.registryPort))
                    dabe = DB()
                    pword = dabe.get_password(self.username)
                    self.login(self.username, pword, self.peerServerPort)
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




# peer is started
main = peerMain()
