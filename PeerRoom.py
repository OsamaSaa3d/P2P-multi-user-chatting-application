import threading
from TextManipulator import TextManipulator
import random
from db import DB
from bcolors import bcolors, colors_used, colors
from vars import has_ended, chat_log
import os
global has_ended
global chat_log
global colors_used
global colors


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
