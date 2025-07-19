from typing import List
from patterns import Pattern

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
