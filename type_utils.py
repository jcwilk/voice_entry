#!/usr/bin/env python3

"""Shared typing logic for type mode - used when typing from recording or clipboard."""

import fcntl
import os
import subprocess
from pathlib import Path
import tempfile
import time
import voice_utils
import log_utils

TYPE_LOCK_FILE = os.path.join(tempfile.gettempdir(), "voice_entry_type.lock")
Path(TYPE_LOCK_FILE).touch(exist_ok=True)


def _type_text(text: str) -> None:
    """Type out text at the current cursor position and press Enter.
    Uses a single xdotool type call with newline appended to avoid timing gaps.
    """
    try:
        # Append newline so type+Enter happen in one invocation - avoids drops when rapid
        subprocess.run(
            ['xdotool', 'type', '--clearmodifiers', '--delay', '1', text + '\n'],
            check=True
        )
    except subprocess.CalledProcessError as e:
        log_utils.log_error(f"Failed to type text: {e}")
    except FileNotFoundError:
        log_utils.log_error("xdotool not found. Please install it to use the type functionality.")


def type_out(text: str, operation: str = "Type") -> None:
    """Type out text at the current cursor position, press Enter, and notify.

    Args:
        text: The text to type out
        operation: Name of the operation for logging/notification
    """
    log_utils.log_info(f"{operation} typing out: {text[:50]}...")
    with open(TYPE_LOCK_FILE, "w") as lockfile:
        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)
        try:
            _type_text(text)
            # Hold the lock briefly so the target app can process the keystrokes
            # before the next queued process starts typing.
            time.sleep(0.2)
        finally:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)
    voice_utils.send_notification(operation, text)
