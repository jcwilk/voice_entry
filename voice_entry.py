#!/usr/bin/env python3

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
import voice_utils
import audio_utils
import log_utils
import time
import os
import threading
import sys
import signal
import pyaudio
import wave
from typing import Optional

def print_and_notify(title: str, text: str) -> None:
    """Log and send a notification."""
    log_utils.log_info(f"{title}: {text}")
    voice_utils.send_notification(title, text)

def handle_completion_signal(signum, frame, state: audio_utils.AudioState):
    """Handle signal to process completion."""
    log_utils.log_info("Received signal to show completion")
    audio_utils.process_audio_and_notify("Completion", voice_utils.get_completion, state)

def handle_edit_signal(signum, frame, state: audio_utils.AudioState):
    """Handle signal to process edit."""
    log_utils.log_info("Received signal to show edit")
    audio_utils.process_audio_and_notify("Edit", lambda text: voice_utils.get_completion(text, mode="edit"), state)

def handle_transcription_signal(signum, frame, state: audio_utils.AudioState):
    """Handle signal to process transcription."""
    log_utils.log_info("Received signal to show transcription")
    audio_utils.process_audio_and_notify("Transcription", lambda text: text, state)

def handle_type_signal(signum, frame, state: audio_utils.AudioState):
    """Handle signal to type out transcription."""
    log_utils.log_info("Received signal to type transcription")
    audio_utils.process_audio_and_notify("Type", lambda text: text, state, should_type=True)

def handle_record_mode():
    """Handle record mode operation."""
    if audio_utils.is_recording():
        # If recording is in progress, treat this as a request for transcription
        log_utils.log_info("Recording in progress, getting transcription...")
        audio_utils.send_signal_to_recording(signal.SIGINT)
        return
    
    # Start new recording
    # Write PID file
    pid = os.getpid()
    with open(audio_utils.PID_FILE, 'w') as f:
        f.write(str(pid))
    log_utils.log_info("No recording in progress, starting new recording...")
    
    try:
        # Initialize state
        state = audio_utils.AudioState()
        
        # Set up signal handlers with state
        signal.signal(signal.SIGUSR1, lambda s, f: handle_completion_signal(s, f, state))
        signal.signal(signal.SIGUSR2, lambda s, f: handle_edit_signal(s, f, state))
        signal.signal(signal.SIGINT, lambda s, f: handle_transcription_signal(s, f, state))
        signal.signal(signal.SIGTERM, lambda s, f: handle_type_signal(s, f, state))
        
        # Start recording in a separate thread
        recording_thread = threading.Thread(target=audio_utils.record_audio, args=(state,))
        recording_thread.daemon = True
        recording_thread.start()
        
        # Notify user
        log_utils.log_info("Recording: Voice recording started...")
        voice_utils.send_notification("Recording", "Voice recording started...")
        
        # Wait for recording thread to finish
        recording_thread.join()
        
    finally:
        # Clean up
        log_utils.log_info("Removing PID file after recording")
        if os.path.exists(audio_utils.PID_FILE):
            os.remove(audio_utils.PID_FILE)

def handle_completion_mode():
    """Handle completion mode operation."""
    if audio_utils.is_recording():
        audio_utils.send_signal_to_recording(signal.SIGUSR1)
    else:
        # Get text from clipboard and process it
        clipboard_text = voice_utils.get_clipboard()
        if not clipboard_text:
            log_utils.log_warning("No text in clipboard")
            return
        
        # Process the clipboard text
        completion = voice_utils.get_completion(clipboard_text)
        if completion:
            voice_utils.set_clipboard(completion)
            voice_utils.send_notification("Completion", completion)
        else:
            log_utils.log_warning("Failed to get completion")

def handle_edit_mode():
    """Handle edit mode operation."""
    if audio_utils.is_recording():
        audio_utils.send_signal_to_recording(signal.SIGUSR2)
    else:
        log_utils.log_warning("No recording in progress")

def handle_type_mode():
    """Handle type mode operation."""
    if audio_utils.is_recording():
        audio_utils.send_signal_to_recording(signal.SIGTERM)
    else:
        log_utils.log_warning("No recording in progress")

def main():
    """Main entry point."""
    log_utils.log_info("Record mode started")
    
    if len(os.sys.argv) < 2:
        log_utils.log_error("No mode specified")
        return
    
    mode = os.sys.argv[1]
    if mode == "record":
        handle_record_mode()
    elif mode == "completion":
        handle_completion_mode()
    elif mode == "edit":
        handle_edit_mode()
    elif mode == "type":
        handle_type_mode()
    else:
        log_utils.log_error(f"Unknown mode: {mode}")

if __name__ == "__main__":
    main()
