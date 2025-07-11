#!/usr/bin/env python3
"""
Terminal Conway's Game of Life
──────────────────────────────
 - Adjustable rows, columns, initial density, and generation interval via CLI.
 - Use --max to fit the board to the current terminal window.
 - Press Ctrl-C to quit at any time.
"""

import argparse
import os
import random
import shutil
import time
from typing import List

CellGrid = List[List[bool]]  # True = alive, False = dead


# ──────────────────────────────────────────────────────────────
#  Game logic
# ──────────────────────────────────────────────────────────────
def next_generation(board: CellGrid) -> CellGrid:
    """Return the next generation by counting the 8 adjacent cells."""
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

            # Apply Conway's rules
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


def render(board: CellGrid, generation: int) -> None:
    """Render the current board state to the terminal."""
    alive = sum(cell for row in board for cell in row)
    header = f"Generation {generation} | Alive {alive}"
    print(header)
    print("-" * len(header))
    for row in board:
        print("".join(LIVE_CELL if cell else DEAD_CELL for cell in row))
    print(flush=True)


# ──────────────────────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────────────────────
def run(rows: int, cols: int, density: float, interval: float) -> None:
    """Run the simulation until interrupted or all cells die."""
    # Create an initial board with random live cells
    board = [[random.random() < density for _ in range(cols)] for _ in range(rows)]

    generation = 0
    try:
        while True:
            clear_screen()
            render(board, generation)

            if all(not cell for row in board for cell in row):
                print("All cells are dead. Exiting.")
                break

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
        help="Fit board to current terminal size (overrides rows and columns)",
    )

    args = parser.parse_args()

    # Override with current terminal size if --max is set
    if args.max:
        term_size = shutil.get_terminal_size(fallback=(80, 24))  # (columns, lines)
        # Reserve 4 lines for header and separator; avoid zero or negative sizes
        args.rows = max(1, term_size.lines - 4)
        args.cols = max(1, term_size.columns)
    run(args.rows, args.cols, args.density, args.interval)


if __name__ == "__main__":
    main()
