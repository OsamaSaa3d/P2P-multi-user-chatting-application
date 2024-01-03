from vars import SYSTEM_IP, SYSTEM_PORT

import socket
import time
import re


class AppStarter:
    def __init__(self):
        self.registryIP = SYSTEM_IP
        self.registryPort = SYSTEM_PORT
        self.tcpClientSocket = None

    def get_registryPort(self):
        return self.registryPort

    def get_tcpClientSocket(self):
        return self.tcpClientSocket

    def establish_connection(self):
        try:
            self.tcpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("\033[96mConnecting, this might take a minute...")
            self.tcpClientSocket.connect((self.registryIP, self.registryPort))
            print("\033[92mConnected Successfully! Loading...\033[0m")
            time.sleep(2)
        except Exception as e:
            return str(e)

    def start_app(self):
        for i in range(3):
            ip_address_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if not ip_address_pattern.match(self.registryIP):
                print("\033[91mInvalid IP address. Try again or enter q to quit.\033[0m")
            else:
                try:
                    self.establish_connection()
                    break
                except:
                    print("\033[91mServer not found or not active. Try again or enter q to quit.\033[0m")