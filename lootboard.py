import curses
import csv
import logging

logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
title = "lootboard"

BOARD_PAD = 4

with open("./user_files/tasks.csv") as csvfile:
    reader = csv.reader(csvfile)
    tasks = list(reader)
    tasks.pop(0)  # Remove the collumn headers


def get_rarity_color(rarity):
    if rarity == "common":
        return curses.color_pair(0)
    elif rarity == "uncommon":
        return curses.color_pair(1)
    elif rarity == "rare":
        return curses.color_pair(2)
    elif rarity == "mythic":
        return curses.color_pair(3)
    else:
        raise Exception(f"unknown rarity: {rarity}")


def main(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)

    selected = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Calculate position to center the lootboard
        max_task_length = max(len(t[0]) for t in tasks)
        board_width = max_task_length + BOARD_PAD
        board_height = len(tasks) + BOARD_PAD
        start_x = (width - board_width) // (BOARD_PAD // 2)
        start_y = (height - board_height) // (BOARD_PAD // 2)

        # Draw title
        stdscr.addstr(
            start_y,
            start_x + (board_width - len(title)) // 2,
            title,
            curses.A_BOLD | curses.A_UNDERLINE,
        )

        for i, task in enumerate(tasks):
            style = curses.A_REVERSE if i == selected else curses.A_NORMAL
            style = style | get_rarity_color(task[1])
            stdscr.addstr(start_y + 2 + i, start_x + 2, task[0], style)

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()
        if key in [curses.KEY_UP, ord("k")] and selected > 0:
            selected -= 1
        elif key in [curses.KEY_DOWN, ord("j")] and selected < len(tasks) - 1:
            selected += 1
        elif key == ord("q"):
            break


if __name__ == "__main__":
    curses.wrapper(main)
