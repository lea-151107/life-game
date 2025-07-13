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
from patterns import PATTERN_LIBRARY, Pattern


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
def clear_screen() -> None:
    """Clear the entire terminal window."""
    os.system("cls" if os.name == "nt" else "clear")


def render(
    board: CellGrid,
    generation: int,
    game_no: int,
    alive: int,
    live_cell: str,
    dead_cell: str,
    rows: int,
    cols: int,
    interval: float,
    endless: bool,
    stagnate_limit: Optional[int],
    density: float,
    fps: float,
    alive_delta: int,
    header_items: str,
    paused: bool,
    edit_mode: bool,
    cursor_y: int,
    cursor_x: int,
    pattern_selection_mode: bool = False,
    placement_mode: bool = False,
    selected_pattern_index: int = 0,
    pattern_names: Optional[List[str]] = None,
    current_pattern_data: Optional[Pattern] = None,
    keep_alive: bool = False,
    pattern_scroll_offset: int = 0,
    search_mode: bool = False,
    search_query: str = "",
) -> None:
    """Render the current board state to the terminal with a detailed header."""
    # ANSI codes for cursor highlighting
    BG_CYAN = "\x1b[46m"
    BG_GREEN = "\x1b[42m"
    FG_BLACK = "\x1b[30m"
    GHOST_CELL = "\x1b[90m" + live_cell + "\x1b[0m"  # Gray
    RESET = "\x1b[0m"

    # --- Header Construction ---
    if not header_items:
        header_items = "game"

    items_to_show = {item.strip() for item in header_items.lower().split(",")}
    header_parts = []

    if "mode" in items_to_show:
        mode_str_parts = []
        if pattern_selection_mode:
            mode_str_parts.append("[Pattern Library]")
        elif placement_mode:
            mode_str_parts.append("[Pattern Placement]")
        elif edit_mode:
            mode_str_parts.append("[Editing]")
        elif paused:
            mode_str_parts.append("[Paused]")

        if endless:
            mode_str_parts.append("[Endless]")
        if keep_alive:
            mode_str_parts.append("[Keep Alive]")
        if stagnate_limit is not None:
            mode_str_parts.append(f"[Stagnate: {stagnate_limit}]")
        if mode_str_parts:
            header_parts.append(" ".join(mode_str_parts))

    if "size" in items_to_show:
        header_parts.append(f"Size: {cols}x{rows}")

    if "interval" in items_to_show:
        header_parts.append(f"Interval: {interval}s")

    if "game" in items_to_show:
        header_parts.append(f"Game {game_no}")

    if "gen" in items_to_show:
        header_parts.append(f"Generation {generation}")

    if "alive" in items_to_show:
        alive_str = f"Alive {alive}"
        if generation > 0:
            alive_str += f" (Δ:{alive_delta:+})"  # Show sign for delta (+/-)
        header_parts.append(alive_str)

    if "density" in items_to_show:
        header_parts.append(f"Density: {density:.1f}%")

    if "fps" in items_to_show:
        header_parts.append(f"FPS: {fps:.1f}")

    header = " | ".join(header_parts)

    # --- Rendering ---
    if header:
        print(header)
        print("-" * len(header))

    if pattern_selection_mode:
        print("Select a pattern using ↑/↓ arrows, press Space to place it.")
        print("Press 'L' or Esc to cancel.")
        print("-" * len(header) if header else "-" * 20)
        if pattern_names:
            # Calculate how many items can be shown
            # Subtract lines for header, separator, and instructions
            header_height = 3 if header else 1 
            instruction_height = 3
            max_items = rows - header_height - instruction_height
            
            # Get the slice of patterns to display
            display_patterns = pattern_names[pattern_scroll_offset:pattern_scroll_offset + max_items]

            for i, name in enumerate(display_patterns, start=pattern_scroll_offset):
                if i == selected_pattern_index:
                    print(f"> {BG_GREEN}{FG_BLACK} {name} {RESET}")
                else:
                    print(f"  {name}")
        
        if search_mode:
            print(f"\nSearch: /{search_query}_")
        return

    ghost_cells = set()
    if placement_mode and current_pattern_data:
        for r_offset, c_offset in current_pattern_data:
            ghost_cells.add((cursor_y + r_offset, cursor_x + c_offset))

    for r, row in enumerate(board):
        line_parts = []
        for c, cell in enumerate(row):
            is_cursor = (edit_mode or placement_mode) and r == cursor_y and c == cursor_x
            is_ghost = (r, c) in ghost_cells

            char_to_render = live_cell if cell else dead_cell
            
            if is_ghost and not cell:
                char_to_render = GHOST_CELL

            if is_cursor:
                line_parts.append(f"{BG_CYAN}{char_to_render}{RESET}")
            else:
                line_parts.append(char_to_render)
        print("".join(line_parts))
    
    if placement_mode:
        print("Move:↑/↓/←/→ | Rotate: R | Flip: F | Place: Space | Cancel: L or Esc", end="")

    print(flush=True)


def render_results(game_no: int, max_generation: int) -> None:
    """Render the final results in a formatted box."""
    title = "Game Over"
    stats = [
        f"Final Game: {game_no}",
        f"Max Generation: {max_generation}",
    ]

    # Determine the width of the box
    width = max(len(s) for s in stats)
    width = max(width, len(title))

    print("\n")
    print(f"┌{'─' * (width + 2)}┐")
    print(f"│ {title.center(width)} │")
    print(f"├{'─' * (width + 2)}┤")
    for stat in stats:
        print(f"│ {stat.ljust(width)} │")
    print(f"└{'─' * (width + 2)}┘")


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


def rotate_pattern(pattern: Pattern, angle: int) -> Pattern:
    """Rotate a pattern by a given angle (90, 180, 270 degrees)."""
    if angle == 0:
        return pattern
    
    rotated_pattern: List[tuple[int, int]] = []
    if angle == 90:
        rotated_pattern = [(c, -r) for r, c in pattern]
    elif angle == 180:
        rotated_pattern = [(-r, -c) for r, c in pattern]
    elif angle == 270:
        rotated_pattern = [(-c, r) for r, c in pattern]
    else:
        return pattern

    # Normalize coordinates to be non-negative
    min_r = min(r for r, c in rotated_pattern) if rotated_pattern else 0
    min_c = min(c for r, c in rotated_pattern) if rotated_pattern else 0
    return [(r - min_r, c - min_c) for r, c in rotated_pattern]


def flip_pattern(pattern: Pattern) -> Pattern:
    """Flip a pattern horizontally."""
    if not pattern:
        return []
    max_c = max(c for _, c in pattern)
    return [(r, max_c - c) for r, c in pattern]


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
    
    # --- Cursor and pattern state ---
    cursor_y, cursor_x = 0, 0
    pattern_names = list(PATTERN_LIBRARY.keys())
    selected_pattern_index = 0
    pattern_scroll_offset = 0
    search_mode = False
    search_query = ""
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
            clear_screen()
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
            user_input = None
            # Determine wait timeout: None (block) if paused, otherwise interval.
            timeout = None if is_static_mode else interval
            if os.name == "nt":
                start_time = time.time()
                while timeout is None or (time.time() - start_time < timeout):
                    if msvcrt.kbhit():
                        user_input = msvcrt.getch()
                        # Arrow keys in Windows are multi-byte sequences (e.g., b'\xe0H')
                        if user_input in (b'\xe0', b'\x00'): 
                            user_input += msvcrt.getch()
                        break
                    if timeout is None:
                        time.sleep(0.05)
                    else:
                        time.sleep(0.01)
            else:  # Unix-like
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if rlist:
                    user_input = sys.stdin.read(1)
                    # Arrow keys in Unix are ANSI escape sequences (e.g., '\x1b[A')
                    if user_input == '\x1b':
                        # Read the rest of the sequence
                        user_input += sys.stdin.read(2)

            # --- Process User Input ---
            # Normalize input to lowercase string
            if isinstance(user_input, bytes):
                try:
                    # Decode bytes and convert to lower case for Windows
                    processed_input = user_input.decode('utf-8').lower()
                except UnicodeDecodeError:
                    # Fallback for special keys that are not valid utf-8 (like arrow keys)
                    processed_input = repr(user_input)
            elif user_input:
                # Convert string to lower case for Unix-like systems
                processed_input = user_input.lower()
            else:
                processed_input = user_input # Keep None as is

            # --- Game Control Keys ---
            if processed_input == 'r' and not placement_mode:
                max_generation = max(max_generation, generation)
                game_no += 1
                board = create_board(rows, cols, density)
                generation = 0
                last_alive_count = 0
                paused = False
                edit_mode = False
                if history is not None: history.clear()
                continue

            if processed_input == 'p':
                paused = not paused
                edit_mode = False
                placement_mode = False
                pattern_selection_mode = False
                if history is not None: history.clear()
                continue

            if paused and not placement_mode and not pattern_selection_mode and processed_input == 'e':
                edit_mode = not edit_mode
                if history is not None: history.clear()
                continue
            
            if paused and not edit_mode and not placement_mode and processed_input == 'l':
                pattern_selection_mode = not pattern_selection_mode
                placement_mode = False
                edit_mode = False
                continue

            # --- Pattern Selection Mode ---
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
                    if processed_input and len(processed_input) == 1 and processed_input.isprintable():
                        search_query += processed_input
                    elif processed_input == repr(b'\x7f') or processed_input == repr(b'\x08'): # Backspace
                        search_query = search_query[:-1]
                    elif processed_input == '\r' or processed_input == '\n': # Enter
                        search_mode = False
                    elif processed_input == '\x1b': # Esc
                        search_mode = False
                        search_query = ""
                    
                    # Reset selection when query changes
                    selected_pattern_index = 0
                    pattern_scroll_offset = 0

                else: # Not in search_mode (i.e., navigating the list)
                    if processed_input == '/':
                        search_mode = True
                        search_query = ""
                    elif processed_input in ('\x1b[a', repr(b'\xe0H')): # Up
                        selected_pattern_index = max(0, selected_pattern_index - 1)
                        if selected_pattern_index < pattern_scroll_offset:
                            pattern_scroll_offset = selected_pattern_index
                    elif processed_input in ('\x1b[b', repr(b'\xe0P')): # Down
                        selected_pattern_index = min(len(display_names) - 1, selected_pattern_index + 1)
                        if selected_pattern_index >= pattern_scroll_offset + max_items:
                            pattern_scroll_offset = selected_pattern_index - max_items + 1
                    elif processed_input == ' ': # Spacebar to select
                        if display_names:
                            pattern_selection_mode = False
                            placement_mode = True
                            pattern_rotation = 0
                            pattern_flip = False

                    elif processed_input == 'l' or processed_input == '\x1b': # 'l' or Esc
                        pattern_selection_mode = False
                continue

            # --- Placement Mode ---
            if placement_mode:
                if processed_input in ('\x1b[a', repr(b'\xe0H')): # Up
                    cursor_y = max(0, cursor_y - 1)
                elif processed_input in ('\x1b[b', repr(b'\xe0P')): # Down
                    cursor_y = min(rows - 1, cursor_y + 1)
                elif processed_input in ('\x1b[d', repr(b'\xe0K')): # Left
                    cursor_x = max(0, cursor_x - 1)
                elif processed_input in ('\x1b[c', repr(b'\xe0M')): # Right
                    cursor_x = min(cols - 1, cursor_x + 1)
                elif processed_input == 'r':
                    pattern_rotation = (pattern_rotation + 90) % 360
                elif processed_input == 'f':
                    pattern_flip = not pattern_flip
                elif processed_input == ' ': # Spacebar to place pattern
                    if display_pattern:
                        for r_offset, c_offset in display_pattern:
                            r, c = cursor_y + r_offset, cursor_x + c_offset
                            if 0 <= r < rows and 0 <= c < cols:
                                board[r][c] = True
                elif processed_input == 'l' or processed_input == '\x1b': # 'l' or Esc
                    placement_mode = False
                continue

            # --- Edit Mode Keys ---
            if edit_mode:
                if processed_input in ('\x1b[a', repr(b'\xe0H')): # Up
                    cursor_y = max(0, cursor_y - 1)
                elif processed_input in ('\x1b[b', repr(b'\xe0P')): # Down
                    cursor_y = min(rows - 1, cursor_y + 1)
                elif processed_input in ('\x1b[d', repr(b'\xe0K')): # Left
                    cursor_x = max(0, cursor_x - 1)
                elif processed_input in ('\x1b[c', repr(b'\xe0M')): # Right
                    cursor_x = min(cols - 1, cursor_x + 1)
                elif processed_input == ' ': # Spacebar to toggle cell state
                    board[cursor_y][cursor_x] = not board[cursor_y][cursor_x]
                
                # In edit mode, we loop back to wait for the next key press
                continue

            # --- Step-through ---
            if paused and processed_input == 'n':
                if history is not None: history.clear()
                # Fall through to the next generation logic
                pass
            elif paused:
                # If paused and any other key is pressed, do nothing.
                continue

            # --- Proceed to next generation ---
            board = next_generation(board)
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
        help="Number of rows.\n"
    )
    parser.add_argument(
        "-c",
        "--cols",
        type=int,
        default=40,
        help="Number of columns.\n"
    )
    parser.add_argument(
        "-d",
        "--density",
        type=float,
        default=0.2,
        help="Initial live-cell density (0–1).\n"
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=0.2,
        help="Delay between generations (seconds).\n"
    )
    parser.add_argument(
        "--max",
        action="store_true",
        help="Fit the board to the current terminal size (overrides rows and columns).\n",
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

    # All argument parsing and pre-run logic is wrapped in a try block
    # to gracefully handle KeyboardInterrupt (Ctrl+C) during setup.
    try:
        args = parser.parse_args()

        # --- Header items validation ---
        VALID_HEADER_KEYWORDS = {
            "mode", "size", "interval", "game", "gen", "alive", "density", "fps"
        }
        if args.header_items:
            # Split by comma, strip whitespace, convert to lower, and remove empty strings
            user_keywords = {
                item.strip().lower() for item in args.header_items.split(',') if item.strip()
            }
            # Find the difference between user's keywords and valid keywords
            invalid_keywords = user_keywords - VALID_HEADER_KEYWORDS
            if invalid_keywords:
                # Sort for consistent and readable error messages
                sorted_invalid = ", ".join(sorted(list(invalid_keywords)))
                sys.exit(f"Error: Invalid keyword(s) in --header-items: {sorted_invalid}")

        if len(args.live_cell) != 1:
            sys.exit("Error: --live-cell must be a single character.")
        if len(args.dead_cell) != 1:
            sys.exit("Error: --dead-cell must be a single character.")

        # --- Stagnate value validation ---
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
            stagnate_limit=effective_stagnate if effective_stagnate > 0 else None,
            live_cell=args.live_cell,
            dead_cell=args.dead_cell,
            header_items=args.header_items,
            keep_alive=args.keep_alive,
        )
    except KeyboardInterrupt:
        # Catch Ctrl+C during the argument parsing or the 5-second wait
        print("\nInterrupted during setup. Exiting.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
