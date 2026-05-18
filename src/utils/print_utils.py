"""Terminal printing helpers used for debug and error output."""

import sys

from webcolors import name_to_rgb

from .colors import Color

DEBUG: bool = False


def print_string_in_color(s: str, color: Color | None = None,
                          new_line: bool = True) -> None:
    """Print a string optionally colored with an ANSI escape code."""
    if new_line:
        end = '\n'
    else:
        end = ''
    try:
        if color is None:
            print(s, end=end)
            return
        rgb = name_to_rgb(color.value)
        print(f"\033[38;2;{rgb.red};{rgb.green};{rgb.blue}m{s}\033[0m",
              end=end)
    except ValueError:
        print(s, end=end)


def print_error(error_msg: str, msg_color: Color = Color.LIGHTCORAL,
                exit_program: bool = True) -> None:
    """Print an error message and optionally exit the program."""
    print_string_in_color(error_msg, msg_color)
    if exit_program:
        sys.exit(1)


def print_debug(s: str, active: bool = DEBUG, new_line: bool = True,
                color: Color | None = Color.PALETURQUOISE) -> None:
    """Print a debug string when debug output is enabled."""
    if not active:
        return
    print_string_in_color(s, color, new_line)
