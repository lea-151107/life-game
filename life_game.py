#!/usr/bin/env python3
"""
Terminal Conway's Game of Life
──────────────────────────────
 - Adjustable rows, columns, initial density, and generation interval via CLI.
 - --max       : Fit the board to the current terminal window.
 - --endless   : Restart automatically with a fresh board when a Dead condition is met.
 - --stagnate N: Treat as Dead if the live-cell count is unchanged for N consecutive generations.
 - Press Ctrl-C to quit at any time.
"""

import argparse
import os
import random
import shutil
import time
from typing import List, Optional

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

            if board[r][c]:
                new_board[r][c] = live_neighbors in (2, 3)
            else:
                new_board[r][c] = live_neighbors == 3
    return new_board


# ──────────────────────────────────────────────────────────────
#  Rendering
# ──────────────────────────────────────────────────────────────
LIVE_CELL = "■"     # Change to "*" if your terminal does not support full-width block
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
#  Main loop
# ──────────────────────────────────────────────────────────────
def create_board(rows: int, cols: int, density: float) -> CellGrid:
    """Generate a new random board."""
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]


def run(
    rows: int,
    cols: int,
    density: float,
    interval: float,
    endless: bool,
    stagnate_limit: Optional[int],
) -> None:
    """
    Run the simulation. A Dead condition is triggered if either:
      1. All cells are dead, or
      2. The live-cell count is unchanged for `stagnate_limit` generations.
    """
    game_no = 1
    board = create_board(rows, cols, density)
    generation = 0
    last_alive: Optional[int] = None
    stagnate_counter = 0

    try:
        while True:
            alive = sum(cell for row in board for cell in row)
            clear_screen()
            render(board, generation, game_no, alive)

            # Dead condition ────────────────────────────────────────────────
            stagnated = (
                stagnate_limit is not None and stagnate_limit > 0 and stagnate_counter >= stagnate_limit
            )
            if alive == 0 or stagnated:
                if endless:
                    time.sleep(interval)
                    game_no += 1
                    board = create_board(rows, cols, density)
                    generation = 0
                    last_alive = None
                    stagnate_counter = 0
                    continue
                else:
                    reason = "All cells are dead." if alive == 0 else "Stagnation detected."
                    print(f"{reason} Exiting.")
                    break

            # Progress to next generation ──────────────────────────────────
            time.sleep(interval)
            board = next_generation(board)
            generation += 1

            # Update stagnation counter
            if last_alive is not None and alive == last_alive:
                stagnate_counter += 1
            else:
                stagnate_counter = 0
            last_alive = alive
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
        help="Fit board to current terminal size (overrides rows and columns)",
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
        help="Treat as Dead if the live-cell count is unchanged for N consecutive generations (0 to disable)",
    )

    args = parser.parse_args()

    # Terminal-size override
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
