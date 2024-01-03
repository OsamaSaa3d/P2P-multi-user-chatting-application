import threading, logging

import threading
import logging

class HelloSender:
    def __init__(self, username, registryIP, registryUDPPort, udpClientSocket):
        self.registryName = registryIP
        self.username = username
        self.registryUDPPort = registryUDPPort
        self.udpClientSocket = udpClientSocket
        self.timer = None

    def send_message(self):
        message = "HELLO " + self.username
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        try:
            self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def start_timer(self):
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

    def sendHelloMessage(self):
        self.send_message()
        self.start_timer()  # Reschedules the sendHelloMessage to execute after 1 second




#class HelloSender:
#    def __init__(self, username, registryIP, registryUDPPort, udpClientSocket ):
#        self.registryName = registryIP
#        self.username = username
#        self.registryUDPPort = registryUDPPort
#        self.loginCredentials = (None, None)
#        self.udpClientSocket = udpClientSocket
#        self.timer = None
#
#    def sendHelloMessage(self):
#        message = "HELLO " + self.username
#        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
#        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
#        self.timer = threading.Timer(1, self.sendHelloMessage)
#        self.timer.start()