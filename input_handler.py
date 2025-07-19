import os
import sys
import time
from enum import Enum, auto
from typing import Optional, Union

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

class Key(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    SELECT = auto()
    CANCEL = auto()
    RESTART = auto()
    PAUSE = auto()
    EDIT = auto()
    PATTERN_MENU = auto()
    TOGGLE_TORUS = auto()
    ROTATE = auto()
    FLIP = auto()
    NEXT_FRAME = auto()
    SEARCH = auto()
    BACKSPACE = auto()
    ENTER = auto()
    DELETE = auto()

# Key mapping for different platforms
KEY_MAP = {
    # Unix-like (ANSI escape codes)
    '\x1b[A': Key.UP,
    '\x1b[B': Key.DOWN,
    '\x1b[D': Key.LEFT,
    '\x1b[C': Key.RIGHT,
    '\x1b': Key.CANCEL,
    '\x7f': Key.BACKSPACE,
    '\x1b[3~': Key.DELETE, # Unix-like for Delete
    '\x08': Key.BACKSPACE,   # ASCII Backspace
    # Windows (msvcrt)
    repr(b'\xe0H'): Key.UP,
    repr(b'\xe0P'): Key.DOWN,
    repr(b'\xe0K'): Key.LEFT,
    repr(b'\xe0M'): Key.RIGHT,
    repr(b'\x08'): Key.BACKSPACE,
    repr(b'\x7f'): Key.BACKSPACE, # Windows for Backspace
    repr(b'\xe0S'): Key.DELETE, # Windows for Delete
    # Common keys
    ' ': Key.SELECT,
    '\r': Key.ENTER,
    '\n': Key.ENTER,
    'r': Key.RESTART,
    'p': Key.PAUSE,
    'e': Key.EDIT,
    'l': Key.PATTERN_MENU,
    't': Key.TOGGLE_TORUS,
    'f': Key.FLIP,
    'n': Key.NEXT_FRAME,
    '/': Key.SEARCH,
}

def get_key(timeout: Optional[float], search_mode: bool = False) -> Optional[Union[Key, str]]:
    """
    Get a key press and convert it to a Key enum or a character.
    Handles platform-specific and multi-byte key codes.
    """
    user_input = None
    if os.name == "nt":
        start_time = time.time()
        while timeout is None or (time.time() - start_time < timeout):
            if msvcrt.kbhit():
                user_input = msvcrt.getch()
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
            # Check for the start of an escape sequence
            if user_input == '\x1b':
                # Read subsequent characters if available, non-blockingly
                while select.select([sys.stdin], [], [], 0)[0]:
                    next_char = sys.stdin.read(1)
                    user_input += next_char
                    # Break on common sequence terminators
                    if next_char.isalpha() or next_char == '~':
                        break

    if user_input is None:
        return None

    # Normalize input to a consistent string format
    if isinstance(user_input, bytes):
        try:
            processed_input = user_input.decode('utf-8').lower()
        except UnicodeDecodeError:
            processed_input = repr(user_input)
    else:
        processed_input = user_input.lower()

    # In search mode, printable characters should be treated as input, not commands.
    if search_mode and len(processed_input) == 1 and processed_input.isprintable():
        return processed_input

    # Check against the key map for commands
    if processed_input in KEY_MAP:
        return KEY_MAP[processed_input]

    # If not a command, return the character if it's printable (for non-search mode)
    if len(processed_input) == 1 and processed_input.isprintable():
        return processed_input

    return None