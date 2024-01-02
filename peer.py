from bcolors import bcolors
from vars import SYSTEM_IP, SYSTEM_PORT
from TextManipulator import TextManipulator
from HelloSender import HelloSender
from AppStarter import AppStarter
from HomeManager import HomeManager
import os
from socket import *
import threading
import time
import logging
import hashlib
import string
import select
from db import DB
import random

global chat_log
chat_log = ''
# Server side of peer

global registryIP
registryIP = SYSTEM_IP
global registryPort
registryPort = SYSTEM_PORT


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
        self.text_manipulator = TextManipulator()
        self.udpPortRoom = None

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
                        peerMain.login(self.username, pword, self.peerServer.peerServerPort)
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


global has_ended
has_ended = False

global colors
colors = [bcolors.LIGHT_GREEN, bcolors.CYAN, bcolors.LIGHT_YELLOW, bcolors.LIGHT_RED, bcolors.YELLOW, bcolors.BLUE]
global colors_used
colors_used = []


class PeerServerRoom(threading.Thread):
    def __init__(self, ipToConnect, udpSock, username, roomname):
        threading.Thread.__init__(self)
        self.udpClientSocket = udpSock
        self.ipToConnect = ipToConnect
        self.username = username
        self.room_name = roomname

    def run(self):
        global chat_log
        global has_ended
        print(f"Receiving {self.room_name} started...")
        # self.udpClientSocket.bind(("localhost", self.udpPort))
        while True:
            if has_ended:
                has_ended = False
                break
            os.system('cls')
            print(chat_log)
            try:
                message, _ = self.udpClientSocket.recvfrom(1024)
                message = message.decode()
                message = message.split("<gL0dDyYi!Z>")
                if len(message) == 1:
                    chat_log = chat_log + message[0] + '\n'
                    continue
                # print(bcolors.GREEN + f"{message[0]}:" + bcolors.ENDC + f"{message[1]}")
                chat_log = chat_log + message[0] + ": " + message[1] + '\n'

            except:
                pass


class PeerClientRoom(threading.Thread):
    def __init__(self, ipToConnect, udpSock, udpPort, ports, username, peerServer, room_name):
        threading.Thread.__init__(self)
        self.udpClientSocket = udpSock
        self.ipToConnect = ipToConnect
        self.ports = ports
        self.username = username
        self.peerServer = peerServer
        self.room_name = room_name
        self.udpPort = udpPort
        self.text_manipulator = TextManipulator()

    def run(self):
        global chat_log
        global has_ended
        global colors_used
        global colors
        print(f"Chat Room {self.room_name} started...")
        random_color = random.randint(0, len(colors))
        while colors[random_color] in colors_used:
            random_color = random.randint(0, len(colors))
        random_color = colors[random_color]
        colors_used.append(random_color)
        # self.udpClientSocket.bind(("localhost", self.udpPort))
        db_obj = DB()
        users_ports = db_obj.get_room_ports(self.room_name)
        self.ports = users_ports[:]
        # message of user entering chat
        notification = bcolors.BLUE + self.username + " has joined the chatroom" + bcolors.ENDC
        for port in self.ports:
            self.udpClientSocket.sendto(notification.encode(), (self.ipToConnect, port))
        while True:
            # os.system('cls')
            # print(chat_log)
            msg = input('')
            if msg == ':q':
                notification = bcolors.LIGHT_MAGENTA + self.username + " has left the chatroom" + bcolors.ENDC
                for port in self.ports:
                    self.udpClientSocket.sendto(notification.encode(), (self.ipToConnect, port))
                self.udpClientSocket.close()
                chat_log = ''
                db_obj.delete_room_online_participants_ports(self.udpPort, self.room_name)
                colors_used.remove(random_color)
                has_ended = True
                break
            msg = self.text_manipulator.manipulate(msg)
            # msg = self.username + "<gL0dDyYi!Z>" + msg #Delimiter: <gL0dDyYi!Z>
            chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + msg + '\n'
            msg = random_color + self.username + bcolors.ENDC + "<gL0dDyYi!Z>" + msg  # Delimiter: <gL0dDyYi!Z>
            users_ports = db_obj.get_room_ports(self.room_name)
            self.ports = users_ports[:]
            os.system('cls')
            print(chat_log)
            if msg != ":q":
                for port in self.ports:
                    if port == self.udpPort:
                        continue
                    try:
                        self.udpClientSocket.sendto(msg.encode(), (self.ipToConnect, port))
                    except:
                        db_obj.delete_room_online_participants_ports(port, self.room_name)


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
                            # print(self.username + ": ", end='')
                            # print(self.chattingClientName + ": " + messageReceived)
                            # print(self.username + ": ")
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
                        peerMain.login(self.username, pword, self.peerServer.peerServerPort)
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
                    # messageSent = f'\033[3m{messageSent}\033[0m' ######WORKS
                    messageSent = self.text_manipulator.manipulate(messageSent)
                    chat_log = chat_log + bcolors.WHITE + self.username + bcolors.ENDC + ": " + messageSent + '\n'
                    # print(messageSent)
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
        self.registryName = registryIP
        self.app_starter = AppStarter()
        self.app_starter.start_app()
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
        self.homeManager = HomeManager()
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
                choice = self.homeManager.start_menu_page()
            else:
                choice = self.homeManager.main_menu_page()

            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username, password_hash = self.homeManager.create_account_page()
                #if password != 'CANCEL':
                self.createAccount(username, password_hash)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username, password_hash = self.homeManager.login_page()
                peerServerPort = self.get_random_port()
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
            elif choice == "3" and not self.isOnline:
                print("\033[92mProgram ended successfully.\033[0m")
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout()
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
                flag_search_for_self = False

                username = input("\033[96mUsername to be searched: \033[0m")
                if username == self.username:
                    print("\033[91mYou cannot search yourself.\033[0m")
                    time.sleep(2)
                    flag_search_for_self = True

                if flag_search_for_self:
                    continue

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
                    # list of online users returned includes user who asks for the list, we remove him from the list
                    online_users = [name for name in response[1:] if name != self.username]
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
                chat_with_self_flag = False
                username = input("\033[96mEnter the username of user to start chat: \033[0m")
                if username == self.username:
                    print("\033[91mYou cannot chat with yourself.\033[0m")
                    chat_with_self_flag = True
                    time.sleep(2)
                if chat_with_self_flag:
                    continue
                searchStatus = self.searchUser(username)
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
                time.sleep(0.2)
                room_name = input("\033[96mEnter the name of the chat room: \033[0m")
                self.create_room(room_name, self.username)
            elif choice == "8" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                room_name = input("\033[96mEnter the name of the chat room: \033[0m")
                self.join_room(room_name, self.username)
            elif choice == "9" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                response = self.get_available_rooms()
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
            elif choice == "10" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
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
                self.serverRoom = PeerServerRoom(registryIP, self.udpClientSocket_room, self.username,
                                                 room_name)
                self.serverRoom.start()
                # self.serverRoom.join()
                self.udpRoom = PeerClientRoom(registryIP, self.udpClientSocket_room, udpPort, response,
                                              self.username,
                                              self.peerServer, room_name)
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
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "join-success":
            print("\033[92mAccount created successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "join-exist":
            print("\033[91mUsername already exists, choose another username. Loading...\033[0m")
            time.sleep(2)

    def create_room(self, room_name, username):
        message = "CREATE-ROOM" + " " + room_name + " " + username
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
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "create-room-success":
            print("\033[92mRoom created successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "create-room-exist":
            print("\033[91mRoom already exists, choose another room name. Loading...\033[0m")
            time.sleep(2)

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

    def join_room(self, room_name, username):
        message = "JOIN-ROOM" + " " + room_name + " " + username
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
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "join-room-success":
            print("\033[92mJoined the room successfully! Loading...\033[0m")
            time.sleep(2)
        elif response == "join-room-not-exist":
            print("\033[91mRoom does not exist, choose another room name. Loading...\033[0m")
            time.sleep(2)
        elif response == "join-room-already-member":
            print("\033[91mYou are already a member of this room. Loading...\033[0m")
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

    def is_port_available_new(self, port):
        taken_ports = self.db.get_all_ports()
        for p in taken_ports:
            if int(p['port']) == int(port) or int(port) == 15500 or int(port) == 15600:
                return False
        return True

    def get_available_port_new(self):
        port = 0
        while True:
            port = random.randint(1024, 65535)
            if self.is_port_available_new(port):
                break
        self.db.create_port(port)
        return port

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

    # get some random avaliable port numbers
    def get_random_port(self):
        port = 0
        while True:  # can be optimized
            port = random.randint(1024, 65535)
            if self.is_port_available(port):
                break
        return port

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

    def get_available_rooms(self):
        message = "GET-AVAILABLE-ROOMS"
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
        return response

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
        return response

    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry


# peer is started
main = peerMain()
