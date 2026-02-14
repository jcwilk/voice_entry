#!/usr/bin/env python3

"""Desktop notification utilities."""

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

from utils import log


def send_notification(title: str, text: str) -> None:
    """Send a desktop notification."""
    Notify.init("Voice Entry")
    notification = Notify.Notification.new(title, text, None)
    notification.show()


def print_and_notify(title: str, text: str) -> None:
    """Log and send a notification."""
    log.log_info(f"{title}: {text}")
    send_notification(title, text)
