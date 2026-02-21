#!/usr/bin/env python3

import os
import tempfile
from typing import Optional

from utils import log
from utils import openai
from utils import xclip

# File paths
PID_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry.pid")


def set_clipboard(text: str) -> None:
    """Copy text to clipboard. Delegates to xclip."""
    xclip.set_clipboard(text)


def get_clipboard() -> Optional[str]:
    """Get text from clipboard. Delegates to xclip."""
    return xclip.get_clipboard()


def get_primary_selection() -> Optional[str]:
    """Get text from primary selection buffer (highlighted text). Delegates to xclip."""
    return xclip.get_primary_selection()


def get_recording_pid() -> Optional[int]:
    """Get the PID of the currently running recording process."""
    if not os.path.exists(PID_FILE):
        log.log_debug("No PID file found")
        return None
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
            log.log_debug(f"Found PID file with PID: {pid}")
            return pid
    except (ValueError, FileNotFoundError) as e:
        log.log_error(f"Error reading PID file: {e}")
        return None


def transcribe_audio(audio_file) -> Optional[str]:
    """Transcribe the audio data and return the text. Delegates to openai module."""
    return openai.transcribe_audio(audio_file)


def get_completion(text: str, mode: str = "context") -> Optional[str]:
    """Send text to OpenAI for completion and return the response. Delegates to openai module."""
    return openai.get_completion(text, mode, get_clipboard=get_clipboard)
