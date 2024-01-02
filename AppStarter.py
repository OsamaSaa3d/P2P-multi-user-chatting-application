from vars import SYSTEM_IP, SYSTEM_PORT


from socket import *
import time
import re

global registryIP
registryIP = SYSTEM_IP


global registryPort
registryPort = SYSTEM_PORT

class AppStarter:
    def __init__(self):
        global registryIP
        global registryPort
        self.registryIP = registryIP
        self.registryPort = registryPort
        self.tcpClientSocket = None

    def get_registryPort(self):
        return self.registryPort

    def get_tcpClientSocket(self):
        return self.tcpClientSocket

    def establish_connection(self):
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        print("\033[96mConnecting, this might take a minute...")
        try:
            self.tcpClientSocket.connect((self.registryIP, self.registryPort))
            print("\033[92mConnected Successfully! Loading...\033[0m")
            time.sleep(2)
        except:
            pass

    def start_app(self):
        #self.registryIP = input("\033[1mEnter IP address of registry: \033[0m")
        #if self.registryIP == "q":
        #    print("\033[92mProgram ended successfully.\033[0m")
        #    exit()
        while True:
            ip_address_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if not ip_address_pattern.match(self.registryIP):
                print("\033[91mInvalid IP address. Try again or enter q to quit.\033[0m")
            else:
                try:
                    self.establish_connection()
                    break
                except:
                    print("\033[91mServer not found or not active. Try again or enter q to quit.\033[0m")