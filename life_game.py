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
--create     : Launch the pattern editor.

Press 'R' to restart the game.
Press Ctrl-C to quit at any time.
"""

import argparse
import os
import shutil
import sys
import time
from collections import deque
from typing import Deque, Optional

from colorama import init as colorama_init

if os.name != "nt":
    import termios
    import tty

from core import create_board, next_generation, is_cyclical
from rendering import render, render_results, render_editor
from input_handler import get_key, Key, get_string_input
from patterns import PATTERN_LIBRARY, Pattern
from utils import rotate_pattern, flip_pattern, extract_pattern_from_board, save_pattern_to_library


def run_pattern_editor(rows: int, cols: int) -> None:
    """Run the interactive pattern editor."""
    board = [[False] * cols for _ in range(rows)]
    cursor_y, cursor_x = rows // 2, cols // 2
    message = "Draw your pattern. Press Enter to save."

    old_settings = None
    if os.name != "nt":
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            render_editor(board, rows, cols, cursor_y, cursor_x, message)
            action = get_key(timeout=None)

            if action == Key.UP:
                cursor_y = max(0, cursor_y - 1)
            elif action == Key.DOWN:
                cursor_y = min(rows - 1, cursor_y + 1)
            elif action == Key.LEFT:
                cursor_x = max(0, cursor_x - 1)
            elif action == Key.RIGHT:
                cursor_x = min(cols - 1, cursor_x + 1)
            elif action == Key.SELECT:
                board[cursor_y][cursor_x] = not board[cursor_y][cursor_x]
            elif action == Key.CANCEL:
                print("Pattern creation cancelled.")
                break
            elif action == Key.ENTER:
                pattern = extract_pattern_from_board(board)
                if not pattern:
                    message = "Pattern is empty. Cannot save."
                    continue

                render_editor(board, rows, cols, -1, -1, "Enter pattern name: ")
                pattern_name = get_string_input()

                if not pattern_name:
                    print("\nPattern name cannot be empty. Aborting.")
                    time.sleep(2)
                    continue

                if save_pattern_to_library(pattern_name, pattern):
                    print(f"\nPattern '{pattern_name}' saved successfully!")
                else:
                    print("\nError: Could not save the pattern.")
                time.sleep(2)
                break

    finally:
        if os.name != "nt" and old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

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
    live_cell: str,
    dead_cell: str,
    header_items: str,
    keep_alive: bool,
    torus: bool,
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
    # --- Mode flags ---
    paused = False
    edit_mode = False
    pattern_selection_mode = False
    placement_mode = False
    torus_mode = torus
    
    # --- Cursor and pattern state ---
    cursor_y, cursor_x = 0, 0
    pattern_names = list(PATTERN_LIBRARY.keys())
    selected_pattern_index = 0
    pattern_scroll_offset = 0
    search_mode = False
    search_query = ""
    search_cursor_pos = 0
    current_pattern_data: Optional[Pattern] = None
    pattern_rotation = 0
    pattern_flip = False


    # --- Terminal setup for non-blocking input ---
    old_settings = None
    if os.name != "nt":
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        last_render_time = time.time()
        fps = 0.0
        last_alive_count = 0

        while True:
            # --- Calculations for rendering ---
            alive = sum(cell for row in board for cell in row)
            alive_delta = alive - last_alive_count
            density_val = (alive / (rows * cols)) * 100 if (rows * cols) > 0 else 0
            
            current_time = time.time()
            time_delta = current_time - last_render_time
            if time_delta > 0:
                fps = 1.0 / time_delta
            last_render_time = current_time

            # --- Prepare pattern for rendering ---
            display_pattern = None
            # Filter patterns based on search query for rendering the list
            if search_query:
                display_names_for_render = [name for name in pattern_names if search_query.lower() in name.lower()]
            else:
                display_names_for_render = pattern_names

            if placement_mode and display_names_for_render:
                selected_name = display_names_for_render[selected_pattern_index]
                pattern = PATTERN_LIBRARY[selected_name]
                if pattern_flip:
                    pattern = flip_pattern(pattern)
                display_pattern = rotate_pattern(pattern, pattern_rotation)

            # --- Render the board ---
            render(
                board,
                generation,
                game_no,
                alive,
                live_cell,
                dead_cell,
                rows,
                cols,
                interval,
                endless,
                stagnate_limit,
                density_val,
                fps,
                alive_delta,
                header_items,
                paused,
                edit_mode,
                cursor_y,
                cursor_x,
                pattern_selection_mode,
                placement_mode,
                selected_pattern_index,
                display_names_for_render, # Use filtered list for rendering
                display_pattern,
                keep_alive,
                pattern_scroll_offset,
                search_mode,
                search_query,
                search_cursor_pos,
                torus_mode,
            )

            # Update for next iteration (only if not in edit mode)
            if not edit_mode and not placement_mode:
                last_alive_count = alive

            # --- Dead condition check (only if not paused/editing) ---
            is_static_mode = paused or edit_mode or placement_mode or pattern_selection_mode
            if not is_static_mode:
                stagnated = False
                if history is not None and len(history) == history.maxlen:
                    if is_cyclical(list(history)):
                        stagnated = True

                if (alive == 0 and not keep_alive) or stagnated:
                    effective_generation = generation
                    if stagnated and stagnate_limit is not None:
                        effective_generation -= stagnate_limit
                    max_generation = max(max_generation, effective_generation)

                    if endless:
                        time.sleep(interval)  # Wait before restarting
                        game_no += 1
                        board = create_board(rows, cols, density)
                        generation = 0
                        last_alive_count = 0
                        if history is not None:
                            history.clear()
                        continue
                    reason = (
                        "All cells are dead."
                        if alive == 0
                        else "Stagnation or two-value oscillation detected."
                    )
                    print(f"{reason} Exiting.")
                    render_results(game_no, max_generation)
                    break

                # Append current state to history before waiting
                if history is not None:
                    history.append(alive)

            # --- Non-blocking input handling ---
            timeout = None if is_static_mode else interval
            action = get_key(timeout, search_mode=search_mode)

            # --- Process User Input ---
            if action is None:
                # No input, proceed to next generation if not paused
                if not is_static_mode:
                    board = next_generation(board, torus=torus_mode)
                    generation += 1
                continue

            # --- Mode-specific input handling ---
            if pattern_selection_mode:
                # Filter patterns based on search query
                if search_query:
                    display_names = [name for name in pattern_names if search_query.lower() in name.lower()]
                else:
                    display_names = pattern_names

                # Calculate visible items for scrolling logic
                header_height = 3 if header_items else 1
                instruction_height = 3
                max_items = rows - header_height - instruction_height

                if search_mode:
                    if isinstance(action, str):
                        search_query = search_query[:search_cursor_pos] + action + search_query[search_cursor_pos:]
                        search_cursor_pos += len(action)
                    elif action == Key.LEFT:
                        search_cursor_pos = max(0, search_cursor_pos - 1)
                    elif action == Key.RIGHT:
                        search_cursor_pos = min(len(search_query), search_cursor_pos + 1)
                    elif action == Key.BACKSPACE:
                        if search_cursor_pos > 0:
                            search_query = search_query[:search_cursor_pos - 1] + search_query[search_cursor_pos:]
                            search_cursor_pos -= 1
                    elif action == Key.DELETE:
                        if search_cursor_pos < len(search_query):
                            search_query = search_query[:search_cursor_pos] + search_query[search_cursor_pos + 1:]
                    elif action == Key.ENTER:
                        search_mode = False
                    elif action == Key.CANCEL:
                        search_mode = False
                        search_query = ""
                    
                    # Reset selection when query changes
                    selected_pattern_index = 0
                    pattern_scroll_offset = 0

                else: # Not in search_mode (i.e., navigating the list)
                    if action == Key.SEARCH:
                        search_mode = True
                        search_query = ""
                        search_cursor_pos = 0
                    elif action == Key.UP:
                        selected_pattern_index = max(0, selected_pattern_index - 1)
                        if selected_pattern_index < pattern_scroll_offset:
                            pattern_scroll_offset = selected_pattern_index
                    elif action == Key.DOWN:
                        selected_pattern_index = min(len(display_names) - 1, selected_pattern_index + 1)
                        if selected_pattern_index >= pattern_scroll_offset + max_items:
                            pattern_scroll_offset = selected_pattern_index - max_items + 1
                    elif action == Key.SELECT: # Spacebar to select
                        if display_names:
                            pattern_selection_mode = False
                            placement_mode = True
                            pattern_rotation = 0
                            pattern_flip = False

                    elif action in (Key.PATTERN_MENU, Key.CANCEL):
                        pattern_selection_mode = False
                continue

            if placement_mode:
                if action == Key.UP:
                    cursor_y = max(0, cursor_y - 1)
                elif action == Key.DOWN:
                    cursor_y = min(rows - 1, cursor_y + 1)
                elif action == Key.LEFT:
                    cursor_x = max(0, cursor_x - 1)
                elif action == Key.RIGHT:
                    cursor_x = min(cols - 1, cursor_x + 1)
                elif action == Key.RESTART_AND_ROTATE:
                    pattern_rotation = (pattern_rotation + 90) % 360
                elif action == Key.FLIP:
                    pattern_flip = not pattern_flip
                elif action == Key.SELECT: # Spacebar to place pattern
                    if display_pattern:
                        for r_offset, c_offset in display_pattern:
                            r, c = cursor_y + r_offset, cursor_x + c_offset
                            if 0 <= r < rows and 0 <= c < cols:
                                board[r][c] = True
                elif action in (Key.PATTERN_MENU, Key.CANCEL):
                    placement_mode = False
                continue

            if edit_mode:
                if action == Key.UP:
                    cursor_y = max(0, cursor_y - 1)
                elif action == Key.DOWN:
                    cursor_y = min(rows - 1, cursor_y + 1)
                elif action == Key.LEFT:
                    cursor_x = max(0, cursor_x - 1)
                elif action == Key.RIGHT:
                    cursor_x = min(cols - 1, cursor_x + 1)
                elif action == Key.SELECT: # Spacebar to toggle cell state
                    board[cursor_y][cursor_x] = not board[cursor_y][cursor_x]
                
                # In edit mode, we loop back to wait for the next key press
                continue

            # --- Global input handling ---
            if action == Key.RESTART_AND_ROTATE:
                max_generation = max(max_generation, generation)
                game_no += 1
                board = create_board(rows, cols, density)
                generation = 0
                last_alive_count = 0
                paused = False
                edit_mode = False
                if history is not None: history.clear()
                continue

            if action == Key.PAUSE:
                paused = not paused
                edit_mode = False
                placement_mode = False
                pattern_selection_mode = False
                if history is not None: history.clear()
                continue

            if paused and action == Key.EDIT:
                edit_mode = True
                if history is not None: history.clear()
                continue
            
            if paused and action == Key.PATTERN_MENU:
                pattern_selection_mode = True
                if history is not None: history.clear()
                continue

            if action == Key.TOGGLE_TORUS:
                torus_mode = not torus_mode
                if history is not None: history.clear()
                continue

            # --- Step-through ---
            if paused and action == Key.NEXT_FRAME:
                if history is not None: history.clear()
                # Fall through to the next generation logic
                pass
            elif paused:
                # If paused and any other key is pressed, do nothing.
                continue

            # --- Proceed to next generation ---
            board = next_generation(board, torus=torus_mode)
            generation += 1

    except KeyboardInterrupt:
        max_generation = max(max_generation, generation)
        print("\nInterrupted by user. Goodbye!")
        render_results(game_no, max_generation)
    finally:
        if os.name != "nt" and old_settings is not None:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


class ArgmentHelpFormatter_(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Console version of Conway's Game of Life.",
        formatter_class=ArgmentHelpFormatter_
    )
    parser.add_argument(
        "-r",
        "--rows",
        type=int,
        default=20,
        help="Number of rows for simulation or editor.\n"
    )
    parser.add_argument(
        "-c",
        "--cols",
        type=int,
        default=40,
        help="Number of columns for simulation or editor.\n"
    )
    parser.add_argument(
        "-d",
        "--density",
        type=float,
        default=0.2,
        help="Initial live-cell density (0–1) for simulation.\n"
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=0.2,
        help="Delay between generations (seconds) for simulation.\n"
    )
    parser.add_argument(
        "--max",
        action="store_true",
        help="Fit the board to the current terminal size (overrides rows and columns).\n",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Launch the pattern editor instead of the simulation.\n",
    )
    parser.add_argument(
        "--torus",
        action="store_true",
        help="Enable torus mode (wraparound edges) for simulation.\n",
    )
    parser.add_argument(
        "--endless",
        action="store_true",
        help="Restart automatically with a fresh board when a Dead condition is met.\n",
    )
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Prevent the game from ending when all cells are dead.\n",
    )
    parser.add_argument(
        "--stagnate",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Dead if the live-cell count shows no new value for N consecutive\n"
            "generations (0 to disable).\n"
            "A value of 5 or greater is recommended for reliable detection.\n"
            "WARNING: This feature may cause any active game to be terminated.\n"
        ),
    )
    parser.add_argument(
        "--live-cell",
        type=str,
        default="■",
        help="Character for a live cell. Must be a single character.\n"
    )
    parser.add_argument(
        "--dead-cell",
        type=str,
        default=" ",
        help="Character for a dead cell. Must be a single character.\n"
    )
    parser.add_argument(
        "--header-items",
        type=str,
        default="game",
        help=(
            "Comma-separated list of items to display in the header.\n"
            "Keywords: mode, size, interval, game, gen, alive, density, fps.\n"
            "Example: --header-items game,gen,alive\n"
        ),
    )

    try:
        colorama_init()
        args = parser.parse_args()

        if len(args.live_cell) != 1:
            sys.exit("Error: --live-cell must be a single character.")
        if len(args.dead_cell) != 1:
            sys.exit("Error: --dead-cell must be a single character.")

        rows, cols = args.rows, args.cols
        if args.max:
            term_size = shutil.get_terminal_size(fallback=(80, 24))
            rows = max(1, term_size.lines - 4)
            cols = max(1, term_size.columns)

        if args.create:
            run_pattern_editor(rows, cols)
            sys.exit(0)

        VALID_HEADER_KEYWORDS = {
            "mode", "size", "interval", "game", "gen", "alive", "density", "fps"
        }
        if args.header_items:
            user_keywords = {item.strip().lower() for item in args.header_items.split(',') if item.strip()}
            invalid_keywords = user_keywords - VALID_HEADER_KEYWORDS
            if invalid_keywords:
                sorted_invalid = ", ".join(sorted(list(invalid_keywords)))
                sys.exit(f"Error: Invalid keyword(s) in --header-items: {sorted_invalid}")

        effective_stagnate = args.stagnate
        if 0 < args.stagnate < 5:
            print(
                f"Warning: --stagnate value of {args.stagnate} is too low for reliable cycle detection.",
                file=sys.stderr
            )
            print("         Setting to the minimum of 5.", file=sys.stderr)
            print("         Starting in 5 seconds... (Press Ctrl+C to cancel)", file=sys.stderr)
            effective_stagnate = 5
            time.sleep(5)

        run(
            rows=rows,
            cols=cols,
            density=args.density,
            interval=args.interval,
            endless=args.endless,
            stagnate_limit=effective_stagnate if effective_stagnate > 0 else None,
            live_cell=args.live_cell,
            dead_cell=args.dead_cell,
            header_items=args.header_items,
            keep_alive=args.keep_alive,
            torus=args.torus,
        )
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()