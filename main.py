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
        self.appManager = AppManager()
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
                choice = self.appManager.start_menu_page()
            else:
                choice = self.appManager.main_menu_page()

            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                self.appManager.create_account_handler()
                #username, password_hash = self.appManager.create_account_page()
                # if password != 'CANCEL':
                #self.createAccount(username, password_hash)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username, password_hash = self.appManager.login_page()
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
                username_for_search = self.appManager.search_user_page()

                searchStatus = self.searchUser(username_for_search)
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print("IP address of " + username_for_search + " is " + searchStatus)
                else:
                    print(f"\033[91mCannot chat with {username_for_search} ...\033[0m")

            # if choice is 5 and user is online, then user is shown the online users
            elif choice == "5" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                response = self.get_online_users()
                self.appManager.online_users_page(response)

            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "6" and self.isOnline:
                os.system('cls')
                time.sleep(0.2)
                username_for_chat = self.appManager.start_chat_page()
                searchStatus = self.searchUser(username_for_chat)
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
                self.serverRoom = PeerServerRoom(registryIP, self.udpClientSocket_room, self.username, room_name)
                self.serverRoom.start()
                # self.serverRoom.join()
                self.udpRoom = PeerClientRoom(registryIP, self.udpClientSocket_room, udpPort, response,
                                              self.username, self.peerServer, room_name)
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
    # def get_random_port(self):
    #    port = 0
    #    while True:  # can be optimized
    #        port = random.randint(1024, 65535)
    #        if self.is_port_available(port):
    #            break
    #    return port

    # checking if port number is available
    # def is_port_available(self, port):
    #    online_users = self.get_online_users()[1:]  # first element is the response code
    #    for user in online_users:
    #        user_port = self.db.get_peer_ip_port(user)[1]
    #        if int(user_port) == int(port):
    #            return False
    #    return True

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