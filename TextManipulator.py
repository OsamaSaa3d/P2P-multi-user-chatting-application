from bcolors import bcolors
import re


class TextManipulator:
    def manipulate(self, message):
        edited_message = message[:]

        matches = re.findall(r'(B\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[1m{match[1]}\033[0m")

        matches = re.findall(r'(I\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[3m{match[1]}\033[0m")

        matches = re.findall(r'(U\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[4m{match[1]}\033[0m")

        matches = re.findall(r'(RED\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[93m{match[1]}\033[0m")

        matches = re.findall(r'(GREEN\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[92m{match[1]}\033[0m")

        matches = re.findall(r'(BLUE\((.*?)\))', edited_message)
        if matches:
            for match in matches:
                edited_message = edited_message.replace(match[0], f"\033[94m{match[1]}\033[0m")

        return edited_message
