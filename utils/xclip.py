#!/usr/bin/env python3

"""Interface to xclip for clipboard and X11 selection buffer operations.

On X11:
- Clipboard (selection 'c'): Ctrl+C / Ctrl+V
- Primary selection (selection 'p'): highlighted text, middle-click paste
"""

import subprocess
from typing import Optional

from utils import log


def get_clipboard() -> Optional[str]:
    """Get text from the clipboard (Ctrl+C buffer)."""
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'c', '-o'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        output, _ = process.communicate()
        if process.returncode != 0:
            return None
        return output.decode('utf-8').strip()
    except Exception as e:
        log.log_error(f"Error reading clipboard: {e}")
        return None


def set_clipboard(text: str) -> None:
    """Copy text to the clipboard (Ctrl+C buffer)."""
    if not text:
        return
    log.log_info(f"Copying to clipboard: {text[:50]}...")
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'c'],
            stdin=subprocess.PIPE,
        )
        process.communicate(text.encode('utf-8'))
    except Exception as e:
        log.log_error(f"Error writing clipboard: {e}")


def get_primary_selection() -> Optional[str]:
    """Get text from the primary selection buffer (highlighted text).

    Returns None if nothing is selected or on error.
    """
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'p', '-o'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        output, _ = process.communicate()
        if process.returncode != 0:
            return None
        text = output.decode('utf-8').strip()
        return text if text else None
    except Exception as e:
        log.log_error(f"Error reading primary selection: {e}")
        return None
