import curses
import logging
import numpy as np
import pickle
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import Counter

DB_FILE = "./data/lootboard.db"
STATE_FILE = "./data/state.pkl"

logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)


class Rarity(Enum):
    COMMON = 0
    RARE = 1
    MYTHIC = 2


RARITY_WEIGHTS = {
    Rarity.COMMON: 70,
    Rarity.RARE: 17,
    Rarity.MYTHIC: 4,
}


@dataclass(frozen=True)
class Task:
    name: str
    rarity: Rarity
    recurring: bool


@dataclass
class State:
    active_tasks: list[tuple[int, bool]]
    reroll_available: bool
    reroll_task: int
    time_created: datetime


def get_rarity_color(rarity):
    if rarity == Rarity.COMMON:
        return curses.color_pair(0)
    elif rarity == Rarity.RARE:
        return curses.color_pair(1)
    elif rarity == Rarity.MYTHIC:
        return curses.color_pair(2)
    else:
        raise Exception(f"Unknown rarity: {rarity}")


def weighted_select(tasks: dict[str, Task], num=4):
    """Select unique task indices based on rarity weights adjusted by rarity count"""

    tasks_arr = list(tasks.values())
    task_ids = list(tasks.keys())

    rarity_counts = Counter(task.rarity for task in tasks_arr)
    # faster to sum RARITY_WEIGHTS using numpy, not worth optimising
    adjusted_weights = np.array(
        [RARITY_WEIGHTS[task.rarity] / rarity_counts[task.rarity] for task in tasks_arr]
    )
    probabilities = adjusted_weights / adjusted_weights.sum()
    selected_indices = np.random.choice(
        len(tasks), size=num, replace=False, p=probabilities
    )

    selected_keys = [task_ids[i] for i in selected_indices]
    return list(zip(selected_keys, [False] * num))


def new_state(tasks: dict[str, Task]):
    active_tasks = weighted_select(tasks)
    reroll_task = active_tasks.pop()
    state = State(
        active_tasks=active_tasks,
        reroll_available=True,
        reroll_task=reroll_task,
        time_created=datetime.now(),
    )
    save_state(state)
    return state


def save_state(state: State):
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "wb") as f:
        pickle.dump(state, f)


def load_state(tasks: dict[str, Task]):
    try:
        with open(STATE_FILE, "rb") as f:
            state = pickle.load(f)

        if not isinstance(state, State):
            raise ValueError("Unpickled object is not an instance of State.")

        # reset the board each day
        if state.time_created.date() != datetime.now().date():
            return new_state(tasks)
        return state

    except (FileNotFoundError, pickle.UnpicklingError):
        logging.info("state not found or invalid")
        return new_state(tasks)


def initialize_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            recurring BOOLEAN NOT NULL,
            UNIQUE(name, rarity)
        )
        """)

        # dump here on complete
        conn.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_id INTEGER,
            name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            recurring BOOLEAN NOT NULL
        )
        """)


# on complete, delete if not recurring and write to completed tasks


initialize_db()


with sqlite3.connect(DB_FILE) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT task_id, name, rarity, recurring FROM tasks")
    rows = cursor.fetchall()
    tasks = {
        row[0]: Task(
            name=row[1],
            rarity=Rarity[row[2].upper()],
            recurring=bool(row[3]),
        )
        for row in rows
    }


def complete_task(id: str, tasks: dict[str, Task]):
    task = tasks[id]

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO completed_tasks (old_id, name, rarity, recurring)
            VALUES (?, ?, ?, ?)
            """,
            (id, task.name, task.rarity.name, task.recurring),
        )

        if not task.recurring:
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (id,))
            conn.commit()
    if not task.recurring:
        del tasks[id]


def main(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    TITLE = "lootboard"
    REROLL = "↻  "

    selected = 0
    state: State = load_state(tasks)

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        PAD = 4
        # Calculate position to center the lootboard
        max_task_length = max(len(task.name) for task in tasks.values())
        board_width = max_task_length + PAD
        board_height = len(state.active_tasks) + PAD
        start_x = (width - board_width) // 2
        start_y = (height - board_height) // 2

        # Draw title
        stdscr.addstr(
            start_y,
            start_x + (board_width - len(TITLE)) // 2,
            TITLE,
            curses.A_BOLD | curses.A_UNDERLINE | curses.color_pair(3),
        )

        # Draw tasks
        for j, (id, is_complete) in enumerate(state.active_tasks):
            style = curses.A_REVERSE if j == selected else curses.A_NORMAL
            if is_complete:
                name = "TASK COMPLETE"
            else:
                task = tasks[id]
                name = task.name
                style = style | get_rarity_color(task.rarity)
            stdscr.addstr(
                start_y + 2 + j,
                start_x + 2 + len(REROLL),
                name,
                style,
            )

        # Draw rerolls
        if state.reroll_available:
            for j, (id,is_complete) in enumerate(state.active_tasks):
                if is_complete:  # if complete
                    continue
                task = tasks[id]
                style = curses.A_NORMAL | curses.color_pair(3)
                stdscr.addstr(start_y + 2 + j, start_x + 2, REROLL, style)

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()
        if key in [curses.KEY_UP, ord("k")] and selected > 0:
            selected -= 1
        elif (
            key in [curses.KEY_DOWN, ord("j")]
            and selected < len(state.active_tasks) - 1
        ):
            selected += 1
        elif key == ord("r") and state.reroll_available:
            # reroll task
            if not state.active_tasks[selected][1]:  # check if incomplete
                state.reroll_available = False
                state.active_tasks[selected] = state.reroll_task
                save_state(state)
        elif key == ord("\n"):
            # complete task (enter key)
            task_id, is_complete = state.active_tasks[selected]
            if not is_complete:
                state.active_tasks[selected] = (None, True)
                save_state(state)
                complete_task(task_id, tasks)

        elif key == ord("x"):
            # FOR DEBUGGING PURPOSES
            state = new_state(tasks)
        elif key == ord("q"):
            break


if __name__ == "__main__":
    curses.wrapper(main)
