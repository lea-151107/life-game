#!/usr/bin/env python3
"""
Terminal Conway's Game of Life
──────────────────────────────
Options
-------
--max        : Fit the board to the current terminal window.
--endless    : Restart automatically with a fresh board when a Dead condition is met.
--stagnate N : Mark as Dead if the live-cell count shows no new value for N generations
               (either all identical or an A-B-A-B… two-value alternation).
Press 'R' to restart the game.
Press Ctrl-C to quit at any time.
"""

import argparse
import os
import random
import shutil
import sys
import time
from collections import deque
from typing import Deque, List, Optional

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty


CellGrid = List[List[bool]]  # True = alive, False = dead


# ──────────────────────────────────────────────────────────────
#  Game logic
# ──────────────────────────────────────────────────────────────
def next_generation(board: CellGrid) -> CellGrid:
    """Return the next generation according to Conway's rules."""
    rows, cols = len(board), len(board[0])
    new_board = [[False] * cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            live_neighbors = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc]:
                        live_neighbors += 1

            new_board[r][c] = (
                live_neighbors in (2, 3) if board[r][c] else live_neighbors == 3
            )
    return new_board


# ──────────────────────────────────────────────────────────────
#  Rendering
# ──────────────────────────────────────────────────────────────
LIVE_CELL = "■"     # Change to "*" if your terminal does not support the full-width block
DEAD_CELL = " "     # Dead cell is rendered as whitespace


def clear_screen() -> None:
    """Clear the entire terminal window."""
    os.system("cls" if os.name == "nt" else "clear")


def render(board: CellGrid, generation: int, game_no: int, alive: int) -> None:
    """Render the current board state to the terminal."""
    header = f"Game {game_no} | Generation {generation} | Alive {alive}"
    print(header)
    print("-" * len(header))
    for row in board:
        print("".join(LIVE_CELL if cell else DEAD_CELL for cell in row))
    print(flush=True)


# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────
def create_board(rows: int, cols: int, density: float) -> CellGrid:
    """Generate a new random board."""
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]


def is_cyclical(seq: List[int]) -> bool:
    """
    Return True if `seq` is composed of a repeating sub-pattern (e.g., A-B-A-B, A-B-C-A-B-C).
    Handles cycles of any length, regardless of the total sequence length.
    """
    n = len(seq)
    # To confirm a cycle of length k, we need at least 2k elements.
    # We check for cycles up to length n/2.
    # A minimum of 4 elements is required to robustly detect a cycle of length 1 or 2.
    if n < 4:
        return False

    # k is the potential cycle length
    for k in range(1, n // 2 + 1):
        is_cycle = True
        # Check if the sequence is consistent with a cycle of length k.
        # We do this by checking if every element is the same as the element k positions before it.
        for i in range(k, n):
            if seq[i] != seq[i - k]:
                is_cycle = False
                break
        if is_cycle:
            # The smallest k that fits the pattern is the cycle length.
            return True
    return False


# ──────────────────────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────────────────────
def run(
    rows: int,
    cols: int,
    density: float,
    interval: float,
    endless: bool,
    stagnate_limit: Optional[int],
) -> None:
    """
    Dead conditions
    ---------------
    1. The number of live cells becomes zero.
    2. The live-cell count enters a repeating cycle (of any length) for
       'stagnate_limit' generations.
    """
    game_no = 1
    max_generation = 0
    board = create_board(rows, cols, density)
    generation = 0
    history: Optional[Deque[int]] = (
        deque(maxlen=stagnate_limit) if stagnate_limit else None
    )

    if os.name != "nt":
        # Set up terminal for non-blocking input on Unix-like systems
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            alive = sum(cell for row in board for cell in row)
            clear_screen()
            render(board, generation, game_no, alive)

            # Dead condition check
            stagnated = False
            if history is not None and len(history) == history.maxlen:
                if is_cyclical(list(history)):
                    stagnated = True

            if alive == 0 or stagnated:
                effective_generation = generation
                if stagnated and stagnate_limit is not None:
                    effective_generation -= stagnate_limit
                max_generation = max(max_generation, effective_generation)

                if endless:
                    time.sleep(interval)  # Wait before restarting
                    game_no += 1
                    board = create_board(rows, cols, density)
                    generation = 0
                    if history is not None:
                        history.clear()
                    continue
                reason = (
                    "All cells are dead."
                    if alive == 0
                    else "Stagnation or two-value oscillation detected."
                )
                print(f"{reason} Exiting.")
                print("\n--- Results ---")
                print(f"Final Game: {game_no}")
                print(f"Max Generation: {max_generation}")
                break

            # Append current state to history before waiting
            if history is not None:
                history.append(alive)

            # Non-blocking wait for interval, checking for 'R' key
            key_pressed_r = False
            if os.name == "nt":
                start_time = time.time()
                while time.time() - start_time < interval:
                    if msvcrt.kbhit():
                        if msvcrt.getch().lower() == b"r":
                            key_pressed_r = True
                            break
                    time.sleep(0.01)
            else:  # Unix-like
                rlist, _, _ = select.select([sys.stdin], [], [], interval)
                if rlist:
                    if sys.stdin.read(1).lower() == "r":
                        key_pressed_r = True

            if key_pressed_r:
                max_generation = max(max_generation, generation)
                game_no += 1
                board = create_board(rows, cols, density)
                generation = 0
                if history is not None:
                    history.clear()
                continue

            # Proceed to next generation
            board = next_generation(board)
            generation += 1
    except KeyboardInterrupt:
        max_generation = max(max_generation, generation)
        print("\nInterrupted by user. Goodbye!")
        print("\n--- Results ---")
        print(f"Final Game: {game_no}")
        print(f"Max Generation: {max_generation}")
    finally:
        if os.name != "nt":
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Console version of Conway's Game of Life",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-r", "--rows", type=int, default=20, help="Number of rows")
    parser.add_argument("-c", "--cols", type=int, default=40, help="Number of columns")
    parser.add_argument(
        "-d", "--density", type=float, default=0.2, help="Initial live-cell density (0–1)"
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=0.2, help="Delay between generations (seconds)"
    )
    parser.add_argument(
        "--max",
        action="store_true",
        help="Fit the board to the current terminal size (overrides rows and columns)",
    )
    parser.add_argument(
        "--endless",
        action="store_true",
        help="Restart automatically with a fresh board when a Dead condition is met",
    )
    parser.add_argument(
        "--stagnate",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Dead if the live-cell count shows no new value for N consecutive "
            "generations (0 to disable)"
        ),
    )

    args = parser.parse_args()

    # Override size with current terminal dimensions if requested
    if args.max:
        term_size = shutil.get_terminal_size(fallback=(80, 24))  # (columns, lines)
        # Reserve three lines for the header and separator
        args.rows = max(1, term_size.lines - 4)
        args.cols = max(1, term_size.columns)

    run(
        rows=args.rows,
        cols=args.cols,
        density=args.density,
        interval=args.interval,
        endless=args.endless,
        stagnate_limit=args.stagnate if args.stagnate > 0 else None,
    )


if __name__ == "__main__":
    main()
