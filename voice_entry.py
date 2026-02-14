#!/usr/bin/env python3

from utils import voice
from utils import audio
from utils import typing
from utils import log
from utils import notification
import time
import os
import threading
import sys
import signal
import pyaudio
import wave
from typing import Optional

def handle_completion_signal(signum, frame, state: audio.AudioState):
    """Handle signal to process completion."""
    log.log_info("Received signal to show completion")
    audio.process_audio_and_notify("Completion", voice.get_completion, state)

def handle_edit_signal(signum, frame, state: audio.AudioState):
    """Handle signal to process edit."""
    log.log_info("Received signal to show edit")
    audio.process_audio_and_notify("Edit", lambda text: voice.get_completion(text, mode="edit"), state)

def handle_transcription_signal(signum, frame, state: audio.AudioState):
    """Handle signal to process transcription."""
    log.log_info("Received signal to show transcription")
    audio.process_audio_and_notify("Transcription", lambda text: text, state)

def handle_type_signal(signum, frame, state: audio.AudioState):
    """Handle signal to type out transcription."""
    log.log_info("Received signal to type transcription")
    audio.process_audio_and_notify("Type", lambda text: text, state, should_type=True)

def handle_record_mode():
    """Handle record mode operation."""
    if audio.is_recording():
        # If recording is in progress, treat this as a request for transcription
        log.log_info("Recording in progress, getting transcription...")
        audio.send_signal_to_recording(signal.SIGINT)
        return
    
    # Start new recording
    # Write PID file
    pid = os.getpid()
    with open(audio.PID_FILE, 'w') as f:
        f.write(str(pid))
    log.log_info("No recording in progress, starting new recording...")
    
    try:
        # Initialize state
        state = audio.AudioState()
        
        # Set up signal handlers with state
        signal.signal(signal.SIGUSR1, lambda s, f: handle_completion_signal(s, f, state))
        signal.signal(signal.SIGUSR2, lambda s, f: handle_edit_signal(s, f, state))
        signal.signal(signal.SIGINT, lambda s, f: handle_transcription_signal(s, f, state))
        signal.signal(signal.SIGTERM, lambda s, f: handle_type_signal(s, f, state))
        
        # Start recording in a separate thread
        recording_thread = threading.Thread(target=audio.record_audio, args=(state,))
        recording_thread.daemon = True
        recording_thread.start()
        
        # Notify user
        log.log_info("Recording: Voice recording started...")
        notification.send_notification("Recording", "Voice recording started...")
        
        # Wait for recording thread to finish
        recording_thread.join()
        
    finally:
        # Clean up
        log.log_info("Removing PID file after recording")
        if os.path.exists(audio.PID_FILE):
            os.remove(audio.PID_FILE)

def handle_completion_mode():
    """Handle completion mode operation."""
    if audio.is_recording():
        audio.send_signal_to_recording(signal.SIGUSR1)
    else:
        # Get text from clipboard and process it
        clipboard_text = voice.get_clipboard()
        if not clipboard_text:
            log.log_warning("No text in clipboard")
            return
        
        # Process the clipboard text
        completion = voice.get_completion(clipboard_text)
        if completion:
            voice.set_clipboard(completion)
            notification.send_notification("Completion", completion)
        else:
            log.log_warning("Failed to get completion")

def handle_edit_mode():
    """Handle edit mode operation."""
    if audio.is_recording():
        audio.send_signal_to_recording(signal.SIGUSR2)
    else:
        log.log_warning("No recording in progress")

def handle_type_mode():
    """Handle type mode operation."""
    if audio.is_recording():
        audio.send_signal_to_recording(signal.SIGTERM)
    else:
        # Type out whatever is currently in the clipboard
        clipboard_text = voice.get_clipboard()
        if not clipboard_text:
            log.log_warning("No text in clipboard")
            return
        
        typing.type_out(clipboard_text)

def main():
    """Main entry point."""
    log.log_info("Record mode started")
    
    if len(os.sys.argv) < 2:
        log.log_error("No mode specified")
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
        log.log_error(f"Unknown mode: {mode}")

if __name__ == "__main__":
    main()
