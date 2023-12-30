import threading
from registryVars import tcpThreads
from registryUDPServer import UDPServer
import db

# db initialization
DB = db.DB()
import logging
class ClientThread(threading.Thread):
    # initializations for client thread
    def __init__(self, ip, port, tcpClientSocket):
        threading.Thread.__init__(self)
        # ip of the connected peer
        self.ip = ip
        # port number of the connected peer
        self.port = port
        # socket of the peer
        self.tcpClientSocket = tcpClientSocket
        # username, online status and udp server initializations
        self.username = None
        self.isOnline = True
        self.udpServer = None
        print("New thread started for " + ip + ":" + str(port))
        # TSL
        # context = ssl.create_default_context()
        # self.tcpClientSocket = context.wrap_socket(self.tcpClientSocket, server_hostname="192.168.1.7")

    # main of the thread
    def run(self):
        # locks for thread which will be used for thread synchronization
        self.lock = threading.Lock()
        print("Connection from: " + self.ip + ":" + str(self.port))
        print("IP Connected: " + self.ip)

        while True:
            try:
                # waits for incoming messages from peers
                message = self.tcpClientSocket.recv(1024).decode().split()
                logging.info("Received from " + self.ip + ":" + str(self.port) + " -> " + " ".join(message))
                #   JOIN    #
                if message[0] == "JOIN":
                    # join-exist is sent to peer,
                    # if an account with this username already exists
                    if DB.is_account_exist(message[1]):
                        response = "join-exist"
                        print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # join-success is sent to peer,
                    # if an account with this username is not exist, and the account is created
                    else:
                        DB.register(message[1], message[2])
                        response = "join-success"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                elif message[0] == "CREATE-ROOM":
                    # checks if the room already exists
                    if DB.is_room_exist(message[1]):
                        response = "create-room-exist"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # if the room does not exist, then creates the room
                    else:
                        DB.create_room(message[1], message[2])
                        response = "create-room-success"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                elif message[0] == "JOIN-ROOM":
                    # checks if the room exists
                    if DB.is_room_exist(message[1]):
                        # checks if the user is already in the room
                        if DB.is_user_in_room(message[2], message[1]):
                            response = "join-room-already-member"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        # if the user is not in the room, then adds the user to the room
                        else:
                            DB.add_user_to_room(message[2], message[1])
                            response = "join-room-success"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                    # if the room does not exist, then sends the related response
                    else:
                        response = "join-room-not-exist"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                elif message[0] == "GET-AVAILABLE-ROOMS":
                    rooms = DB.get_all_rooms()
                    response = "get-available-rooms-success"
                    for room in rooms:
                        response += " " + room['room_name']
                    logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                    self.tcpClientSocket.send(response.encode())

                #   LOGIN    #
                elif message[0] == "LOGIN":
                    # login-account-not-exist is sent to peer,
                    # if an account with the username does not exist
                    if not DB.is_account_exist(message[1]):
                        response = "login-account-not-exist"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # login-online is sent to peer,
                    # if an account with the username already online
                    elif DB.is_account_online(message[1]):
                        response = "login-online"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # login-success is sent to peer,
                    # if an account with the username exists and not online
                    else:
                        # retrieves the account's password, and checks if the one entered by the user is correct
                        retrievedPass = DB.get_password(message[1])
                        # if password is correct, then peer's thread is added to threads list
                        # peer is added to DB with its username, port number, and ip address
                        if retrievedPass == message[2]:
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username] = self
                            finally:
                                self.lock.release()

                            DB.user_login(message[1], self.ip, message[3])
                            # login-success is sent to peer,
                            # and a udp server thread is created for this peer, and thread is started
                            # timer thread of the udp server is started
                            response = "login-success"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                            self.udpServer = UDPServer(self.username, self.tcpClientSocket)
                            self.udpServer.start()
                            self.udpServer.timer.start()
                        # if password not matches and then login-wrong-password response is sent
                        else:
                            response = "login-wrong-password"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                #   LOGOUT  #
                elif message[0] == "LOGOUT":
                    # if user is online,
                    # removes the user from onlinePeers list
                    # and removes the thread for this user from tcpThreads
                    # socket is closed and timer thread of the udp for this
                    # user is cancelled
                    print(message)
                    if len(message) > 1 and message[1] is not None and DB.is_account_online(message[1]):
                        DB.user_logout(message[1])
                        self.lock.acquire()
                        try:
                            if message[1] in tcpThreads:
                                del tcpThreads[message[1]]
                        finally:
                            self.lock.release()
                        print(self.ip + ":" + str(self.port) + " is logged out")
                        self.tcpClientSocket.close()
                        self.udpServer.timer.cancel()
                        break
                    else:
                        self.tcpClientSocket.close()
                        break

                #   SEARCH  #
                elif message[0] == "SEARCH":
                    # checks if an account with the username exists
                    if DB.is_account_exist(message[1]):
                        # checks if the account is online
                        # and sends the related response to peer
                        if DB.is_account_online(message[1]):
                            peer_info = DB.get_peer_ip_port(message[1])
                            response = "search-success " + peer_info[0] + ":" + peer_info[1]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "search-user-not-online"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                    # enters if username does not exist
                    else:
                        response = "search-user-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "SEARCH-ROOM-USERS":
                    # checks if the room exists
                    if DB.is_room_exist(message[1]):
                        # retrieves the room's participants
                        participants = DB.get_room_participants(message[1])
                        if message[2] in participants:
                            response = "search-user-room-success"
                        else:
                            response = "search-user-room-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "ROOM-PEERS":
                    if DB.is_room_exist(message[1]):
                        users_ports = DB.get_room_ports(message[1])
                        # DB.add_port_to_room(message[1], int(message[3]))
                        response = "room-peers-success" + " "
                        for user_port in users_ports:
                            response += str(user_port) + " "
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        print(response)
                        self.tcpClientSocket.send(response.encode())
                elif message[0] == "ROOM-PEERS-ADD":
                    if DB.is_room_exist(message[1]):
                        DB.add_port_to_room(message[1], int(message[2]))
                        response = "room-peers-add-success"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())


                #   GET-ONLINE-USERS    #
                elif message[0] == "GET-ONLINE-USERS":
                    # if there is no online user, then sends no-online-user response
                    if len(tcpThreads) == 0:
                        response = "no-online-users"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # if there are online users, then sends the list of online users
                    else:
                        response = "get-online-users-success " + " ".join(tcpThreads.keys())
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))

                # function for resettin the timeout for the udp timer thread

    def resetTimeout(self):
        self.udpServer.resetTimer()