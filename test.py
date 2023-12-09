import curses
import time

# positioning text and manipulating the cursor
# def main(stdscr):
#     stdscr.addstr(5, 10, "Press a key:")
#     stdscr.refresh()
#     key = stdscr.getch()
#     stdscr.addstr(7, 10, f"You pressed: {chr(key)}")
#     stdscr.refresh()
#     stdscr.getch()

# curses.wrapper(main)

# coloring text with background and foreground colors
# def main(stdscr):
#     curses.start_color()
#     curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)

#     stdscr.addstr(5, 10, "Colored Text!", curses.color_pair(1))
#     stdscr.refresh()
#     stdscr.getch()

# curses.wrapper(main)


# creating a window
# def main(stdscr):
#     h, w = stdscr.getmaxyx()
#     window1 = curses.newwin(h//2, w, 0, 0)
#     window2 = curses.newwin(h//2, w, h//2, 0)

#     window1.addstr(0, 0, "Window 1")
#     window2.addstr(0, 0, "Window 2")

#     window1.refresh()
#     window2.refresh()

#     stdscr.getch()

# curses.wrapper(main)


def main(stdscr):
    stdscr.addstr(5, 10, "Dynamic Updates! Wait for 2 seconds...")
    stdscr.refresh()
    time.sleep(2)

    stdscr.addstr(7, 10, "Updated Text!")
    stdscr.refresh()
    stdscr.getch()

curses.wrapper(main)

# text formatting
# https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
# print("\033[1mThis is bold text.\033[0m")
# print("\033[3mThis is italic text.\033[0m")
# print("\033[4mThis is underlined text.\033[0m")
# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKCYAN = '\033[96m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'