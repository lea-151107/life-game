from typing import List, Optional

from utils import CellGrid, Pattern

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
    search_cursor_pos: int = 0,
    torus: bool = False,
) -> None:
    """Render the current board state to the terminal with a detailed header."""
    output_buffer = []
    # ANSI escape code to move cursor to top-left and clear screen
    output_buffer.append("\x1b[H\x1b[J")

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
        if torus:
            mode_str_parts.append("[Torus]")
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
        output_buffer.append(header)
        output_buffer.append("-" * len(header))

    if pattern_selection_mode:
        output_buffer.append("Select a pattern using ↑/↓ arrows, press Space to place it.")
        output_buffer.append("Press 'L' or Esc to cancel.")
        output_buffer.append("-" * len(header) if header else "-" * 20)
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
                    output_buffer.append(f"> {BG_GREEN}{FG_BLACK} {name} {RESET}")
                else:
                    output_buffer.append(f"  {name}")

        if search_mode:
            # Build the search string with a cursor
            pre_cursor = search_query[:search_cursor_pos]
            cursor_char = search_query[search_cursor_pos] if search_cursor_pos < len(search_query) else ' '
            post_cursor = search_query[search_cursor_pos+1:]
            search_display = f"{pre_cursor}{BG_CYAN}{cursor_char}{RESET}{post_cursor}"
            output_buffer.append(f"\nSearch: /{search_display}")
        
        print("\n".join(output_buffer), flush=True)
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
        output_buffer.append("".join(line_parts))

    if placement_mode:
        # Use print without newline to keep it on the same line as the board
        print("\n".join(output_buffer), flush=True)
        print("Move:↑/↓/←/→ | Rotate: R | Flip: F | Place: Space | Cancel: L or Esc", end="", flush=True)
    else:
        print("\n".join(output_buffer), flush=True)


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

def render_editor(board: CellGrid, rows: int, cols: int, cursor_y: int, cursor_x: int, message: str) -> None:
    """Render the pattern editor UI."""
    output_buffer = []
    output_buffer.append("\x1b[H\x1b[J")  # Clear screen

    BG_CYAN = "\x1b[46m"
    RESET = "\x1b[0m"
    LIVE_CELL = "■"
    DEAD_CELL = " "

    title = "Pattern Editor"
    output_buffer.append(title)
    output_buffer.append("-" * len(title))

    for r, row in enumerate(board):
        line_parts = []
        for c, cell in enumerate(row):
            char_to_render = LIVE_CELL if cell else DEAD_CELL
            if r == cursor_y and c == cursor_x:
                line_parts.append(f"{BG_CYAN}{char_to_render}{RESET}")
            else:
                line_parts.append(char_to_render)
        output_buffer.append("".join(line_parts))
    
    output_buffer.append("-" * cols)
    output_buffer.append(message)
    output_buffer.append("Move:↑/↓/←/→ | Toggle: Space | Save: Enter | Quit: Esc")

    print("\n".join(output_buffer), flush=True)