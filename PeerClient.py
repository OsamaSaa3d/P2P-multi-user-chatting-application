import threading
import logging
import time
import os
from TextManipulator import TextManipulator
from socket import *
from db import DB
from vars import SYSTEM_IP, SYSTEM_PORT
from bcolors import bcolors

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
                        self.tcpClientSocket.connect((SYSTEM_IP, SYSTEM_PORT))
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


