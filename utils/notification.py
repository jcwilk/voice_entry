#!/usr/bin/env python3

"""Desktop notification utilities."""

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

from utils import log


def _wrap_text(text: str, width: int = 55) -> str:
    """Insert newlines so notification body wraps instead of truncating."""
    words = text.replace("\n", " ").split()
    lines, current = [], []
    length = 0
    for w in words:
        if length + len(w) + (1 if current else 0) > width and current:
            lines.append(" ".join(current))
            current, length = [w], len(w)
        else:
            current.append(w)
            length += len(w) + (1 if len(current) > 1 else 0)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines[:10])  # Limit lines; daemons often cap display


def send_notification(title: str, text: str, wrap: bool = True) -> None:
    """Send a desktop notification."""
    Notify.init("Voice Entry")
    body = _wrap_text(text) if wrap and text else text
    notification = Notify.Notification.new(title, body, None)
    notification.show()


def print_and_notify(title: str, text: str) -> None:
    """Log and send a notification."""
    log.log_info(f"{title}: {text}")
    send_notification(title, text)
