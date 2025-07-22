import random
from typing import List

from utils import CellGrid

def next_generation(board: CellGrid, torus: bool = False) -> CellGrid:
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
                    if torus:
                        nr %= rows
                        nc %= cols
                        live_neighbors += board[nr][nc]
                    elif 0 <= nr < rows and 0 <= nc < cols and board[nr][nc]:
                        live_neighbors += 1

            new_board[r][c] = (
                live_neighbors in (2, 3) if board[r][c] else live_neighbors == 3
            )
    return new_board

def create_board(rows: int, cols: int, density: float) -> CellGrid:
    """Generate a new random board."""
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]

def is_cyclical(seq: List[int]) -> bool:
    """
    Return True if `seq` is composed of a repeating sub-pattern (e.g., A-B-A-B, A-B-C-A-B-C).
    Handles cycles of any length, regardless of the total sequence length.
    """
    n = len(seq)
    if n < 4:
        return False

    for k in range(1, n // 2 + 1):
        is_cycle = True
        for i in range(k, n):
            if seq[i] != seq[i - k]:
                is_cycle = False
                break
        if is_cycle:
            return True
    return False
