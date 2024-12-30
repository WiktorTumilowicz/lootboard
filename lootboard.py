import curses
import csv
import logging
import numpy as np

from dataclasses import dataclass
from enum import Enum
from collections import Counter


class Rarity(Enum):
    COMMON = 0
    RARE = 1
    MYTHIC = 2


RARITY_WEIGHTS = {
    Rarity.COMMON: 70,
    Rarity.RARE: 17,
    Rarity.MYTHIC: 3,
}


@dataclass(frozen=True)
class Task:
    name: str
    rarity: Rarity
    recurring: bool


logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)


def get_rarity_color(rarity):
    if rarity == Rarity.COMMON:
        return curses.color_pair(0)
    elif rarity == Rarity.RARE:
        return curses.color_pair(2)
    elif rarity == Rarity.MYTHIC:
        return curses.color_pair(3)
    else:
        raise Exception(f"Unknown rarity: {rarity}")


def weighted_select(tasks, num=3):
    """Select unique task indices based on rarity weights adjusted by rarity count"""
    rarity_counts = Counter(task.rarity for task in tasks)
    adjusted_weights = np.array(
        [RARITY_WEIGHTS[task.rarity] / rarity_counts[task.rarity] for task in tasks]
    )
    # faster to sum RARITY WEIGHTS using numpy
    probabilities = adjusted_weights / adjusted_weights.sum()
    selected_indices = np.random.choice(
        len(tasks), size=num, replace=False, p=probabilities
    )
    return selected_indices.tolist()


with open("./user_files/tasks.csv") as csvfile:
    tasks = [
        Task(
            name=row[0],
            rarity=Rarity[row[1].upper()],
            recurring=row[2].lower() == "true",
        )
        for i, row in enumerate(csv.reader(csvfile))
        if i > 0  # Skip header row
    ]


def main(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)

    selected = 0
    task_indicies = weighted_select(tasks)

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = "lootboard"
        BOARD_PAD = 4

        # Calculate position to center the lootboard
        max_task_length = max(len(task.name) for task in tasks)
        board_width = max_task_length + BOARD_PAD
        board_height = len(tasks) + BOARD_PAD
        start_x = (width - board_width) // (BOARD_PAD // 2)
        start_y = (height - board_height) // (BOARD_PAD // 2)

        # Draw title
        stdscr.addstr(
            start_y,
            start_x + (board_width - len(title)) // 2,
            title,
            curses.A_BOLD | curses.A_UNDERLINE | curses.color_pair(1),
        )

        for j, idx in enumerate(task_indicies):
            task = tasks[idx]
            style = curses.A_REVERSE if j == selected else curses.A_NORMAL
            style = style | get_rarity_color(task.rarity)
            stdscr.addstr(start_y + 2 + j, start_x + 2, task.name, style)

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
