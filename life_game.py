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
Press Ctrl-C to quit at any time.
"""

import argparse
import os
import random
import shutil
import time
from collections import deque
from typing import Deque, List, Optional

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


def two_value_alternation(seq: List[int]) -> bool:
    """
    Return True if 'seq' alternates between exactly two distinct values (A-B-A-B…).
    Assumes len(seq) >= 2.
    """
    if len(set(seq)) != 2:
        return False
    even_vals = {seq[i] for i in range(0, len(seq), 2)}
    odd_vals = {seq[i] for i in range(1, len(seq), 2)}
    return len(even_vals) == len(odd_vals) == 1 and even_vals != odd_vals


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
    2. The live-cell count shows no new value for 'stagnate_limit' generations, i.e.:
       a) all values identical, or
       b) an A-B-A-B… two-value alternation.
    """
    game_no = 1
    board = create_board(rows, cols, density)
    generation = 0
    history: Optional[Deque[int]] = (
        deque(maxlen=stagnate_limit) if stagnate_limit else None
    )

    try:
        while True:
            alive = sum(cell for row in board for cell in row)
            clear_screen()
            render(board, generation, game_no, alive)

            # Dead condition check
            stagnated = False
            if history is not None and len(history) == history.maxlen:
                if len(set(history)) == 1:
                    stagnated = True
                elif two_value_alternation(list(history)):
                    stagnated = True

            if alive == 0 or stagnated:
                if endless:
                    time.sleep(interval)
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
                break

            # Proceed to next generation
            if history is not None:
                history.append(alive)
            time.sleep(interval)
            board = next_generation(board)
            generation += 1
    except KeyboardInterrupt:
        print("\nInterrupted by user. Goodbye!")


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
        default=10,
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
        # Reserve 4 lines for header and separator; avoid zero or negative sizes
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
