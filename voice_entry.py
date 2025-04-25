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
from typing import Optional

def print_and_notify(title: str, text: str) -> None:
    """Log and send a notification."""
    log_utils.log_info(f"{title}: {text}")
    voice_utils.send_notification(title, text)

def handle_record_mode() -> None:
    """Handle recording mode."""
    log_utils.log_info("Record mode started")
    
    if audio_utils.is_recording():
        log_utils.log_info("Recording in progress, sending stop signal...")
        # Send signal to stop recording
        audio_utils.send_signal_to_recording(signal.SIGINT)
    else:
        log_utils.log_info("No recording in progress, starting new recording...")
        
        # Write PID file before starting recording
        with open(voice_utils.PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            # Set up signal handlers
            audio_utils.setup_signal_handlers()
            
            # Start recording in a separate thread
            recording_thread = threading.Thread(target=audio_utils.record_audio)
            recording_thread.daemon = True
            recording_thread.start()
            
            # Show recording notification
            print_and_notify("Recording", "Voice recording started...")
            
            # Wait for recording to complete
            recording_thread.join()
            
        finally:
            # Only remove PID file if we're the ones who created it
            if os.path.exists(voice_utils.PID_FILE):
                try:
                    with open(voice_utils.PID_FILE, 'r') as f:
                        if int(f.read().strip()) == os.getpid():
                            log_utils.log_info("Removing PID file after recording")
                            os.remove(voice_utils.PID_FILE)
                except (ValueError, FileNotFoundError) as e:
                    log_utils.log_error(f"Error handling PID file: {e}")

def handle_completion_mode() -> None:
    """Handle completion mode."""
    log_utils.log_info("Completion mode started")
    
    # Check if there's a recording in progress
    pid = voice_utils.get_recording_pid()
    if pid is not None:
        log_utils.log_info(f"Found recording in progress with PID {pid}")
        # Send completion menu signal to the recording process
        audio_utils.send_signal_to_recording(signal.SIGUSR1)

def handle_edit_mode() -> None:
    """Handle edit mode."""
    log_utils.log_info("Edit mode started")
    
    # Check if there's a recording in progress
    pid = voice_utils.get_recording_pid()
    if pid is not None:
        log_utils.log_info(f"Found recording in progress with PID {pid}")
        # Send edit menu signal to the recording process
        audio_utils.send_signal_to_recording(signal.SIGUSR2)

def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python voice_entry.py [record|completion|edit]")
        sys.exit(1)
        
    mode = sys.argv[1].lower()
    if mode == "record":
        handle_record_mode()
    elif mode == "completion":
        handle_completion_mode()
    elif mode == "edit":
        handle_edit_mode()
    else:
        print("Invalid mode. Use 'record', 'completion', or 'edit'")
        sys.exit(1)

if __name__ == "__main__":
    main()
