import curses

tasks = ["Daily Quest 1aasdsas", "Daily Quest 2", "Random Reward"]
title = "lootboard"

BOARD_PAD = 4


def main(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    selected = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Calculate the position to center the lootboard
        max_task_length = max(len(task) for task in tasks)
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
            stdscr.addstr(start_y + 2 + i, start_x + 2, task, style)

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
