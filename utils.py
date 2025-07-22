import json
from typing import List, Tuple

Pattern = List[Tuple[int, int]]
CellGrid = List[List[bool]]

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

def save_pattern_to_library(name: str, pattern: Pattern, library: dict) -> bool:
    """Adds a pattern to the library and saves it to the JSON file."""
    library[name] = pattern
    try:
        with open("patterns.json", "w", encoding="utf-8") as f:
            json.dump(library, f, indent=4)
        return True
    except (IOError, TypeError):
        return False

