
from socket import *
import netifaces as ni

hostname = gethostname()
try:
    host = gethostbyname(hostname)
except gaierror:
    host = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

global SYSTEM_IP
SYSTEM_IP = host