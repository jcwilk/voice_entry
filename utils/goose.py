#!/usr/bin/env python3

"""Invoke Goose AI agent with text - used when feeding from recording or clipboard."""

import json
import os
import shlex
import subprocess
import tempfile
import time
from utils import log
from utils import notification


def _extract_last_assistant_message(json_str: str) -> str:
    """Extract the text from the last assistant message in Goose JSON output."""
    try:
        data = json.loads(json_str)
        for m in reversed(data.get("messages", [])):
            if m.get("role") == "assistant":
                parts = []
                for c in m.get("content", []):
                    if c.get("type") == "text":
                        parts.append(c.get("text", ""))
                return "".join(parts)
        return ""
    except (json.JSONDecodeError, TypeError):
        return ""


def _set_clipboard(text: str) -> None:
    """Set clipboard - wl-copy on Wayland, xclip on X11 (must stay running for X11)."""
    if not text:
        return
    # wl-copy persists; on X11 xclip must stay running (-loops 1) or selection is lost when we exit
    try:
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"), timeout=5)
        if p.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # X11: run xclip -loops 1 detached so it survives our exit and keeps selection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        subprocess.Popen(
            ["setsid", "sh", "-c", f"xclip -selection c -loops 1 < {shlex.quote(path)} & sleep 2; rm -f {shlex.quote(path)}"],
            start_new_session=True,
        )
        time.sleep(2)  # Let xclip read file and claim selection before we exit
    except FileNotFoundError:
        # No setsid or xclip - fall back to plain xclip (may not persist)
        try:
            p = subprocess.Popen(["xclip", "-selection", "c"], stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"), timeout=5)
        except FileNotFoundError:
            pass
    finally:
        try:
            os.unlink(path)
        except (OSError, NameError):
            pass


def run_goose(text: str) -> None:
    """Run Goose with the given text as instructions.

    Uses an isolated run (--no-session) so it doesn't interact with existing
    desktop or interactive sessions. Ensures the developer extension is enabled.
    Extracts the last assistant message and puts it on the clipboard.

    Args:
        text: The instruction text to send to Goose (from transcription or clipboard).
    """
    if not text or not text.strip():
        log.log_warning("Empty text for Goose, skipping")
        return

    log.log_info(f"Running Goose with: {text[:80]}...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(text.strip())
        inst_path = f.name

    try:
        result = subprocess.run(
            [
                "goose", "run",
                "--no-session",
                "--with-builtin", "developer,fetch,skills",
                "-q", "--output-format", "json",
                "-i", inst_path,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
            env={**os.environ},
        )
        last_msg = ""
        if result.stdout:
            last_msg = _extract_last_assistant_message(result.stdout)
        if last_msg:
            _set_clipboard(last_msg)
            log.log_info(f"Copied to clipboard: {last_msg[:50]}...")
            notification.send_notification("Goose", last_msg)
    except FileNotFoundError:
        log.log_error("goose not found. Install it: https://github.com/block/goose")
    except Exception as e:
        log.log_error(f"Failed to run Goose: {e}")
    finally:
        try:
            os.unlink(inst_path)
        except OSError:
            pass
