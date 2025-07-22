from typing import List
from patterns import Pattern, CellGrid

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

def extract_pattern_from_board(board: CellGrid) -> Pattern:
    """Extracts and normalizes a pattern from the board."""
    live_cells = []
    for r, row in enumerate(board):
        for c, cell in enumerate(row):
            if cell:
                live_cells.append((r, c))

    if not live_cells:
        return []

    min_r = min(r for r, c in live_cells)
    min_c = min(c for r, c in live_cells)

    return [(r - min_r, c - min_c) for r, c in live_cells]

def save_pattern_to_library(name: str, pattern: Pattern) -> bool:
    """Appends a new pattern to the PATTERN_LIBRARY in patterns.py."""
    try:
        with open("patterns.py", "r+", encoding="utf-8") as f:
            lines = f.readlines()
            
            # Find the end of the dictionary
            for i, line in reversed(list(enumerate(lines))):
                if "}" in line:
                    closing_brace_line = i
                    break
            else:
                return False # Dictionary end not found

            # Format the new pattern entry
            new_pattern_str = f'    "{name}": {pattern},\n'

            # Insert the new pattern before the closing brace
            lines.insert(closing_brace_line, new_pattern_str)

            # Go back to the beginning of the file and write the modified lines
            f.seek(0)
            f.writelines(lines)
            f.truncate()
        return True
    except (IOError, IndexError, UnicodeEncodeError):
        return False

