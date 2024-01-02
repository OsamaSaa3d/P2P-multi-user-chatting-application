from socket import *
import threading
import logging


class HelloSender:
    def __init__(self, username, registryIP, registryUDPPort, udpClientSocket, ):
        self.registryName = registryIP
        self.username = username
        self.registryUDPPort = registryUDPPort
        self.loginCredentials = (None, None)
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.timer = None

    def sendHelloMessage(self):
        message = "HELLO " + self.username
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()
