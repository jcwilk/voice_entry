#!/usr/bin/env python3

import os
import pyaudio
import wave
import time
from typing import List, Optional
import voice_utils
import log_utils
import threading
import tempfile
import signal
import tkinter as tk

# File paths
AUDIO_FILE_NAME: str = os.path.join(tempfile.gettempdir(), "voice_entry_audio.wav")
PID_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry.pid")
TEXT_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry_text.txt")
RAW_AUDIO_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry_raw.wav")

# Global audio variables
_stream = None
_audio = None
_wave_file = None
_recording = False
_lock = threading.Lock()

def handle_completion_menu(signum, frame):
    """Handle signal to stop recording and show completion."""
    global _stream, _audio, _wave_file, _recording
    log_utils.log_info("Received signal to stop recording")
    
    with _lock:
        _recording = False
        # Stop recording
        if _stream is not None:
            log_utils.log_info("Stopping recording")
            _stream.stop_stream()
            _stream.close()
            _stream = None
        
        if _audio is not None:
            _audio.terminate()
            _audio = None
        
        if _wave_file is not None:
            _wave_file.close()
            _wave_file = None
    
    # Save the recorded audio
    save_audio()
    
    # Transcribe the audio
    text = voice_utils.transcribe_audio()
    if not text:
        log_utils.log_error("No transcription available")
        return
    
    # Get completion from OpenAI
    completion = voice_utils.get_completion(text)
    if not completion:
        log_utils.log_error("Failed to get completion from OpenAI")
        return
    
    # Copy completion to clipboard and notify
    voice_utils.set_clipboard(completion)
    log_utils.log_info(f"Completion copied to clipboard: {completion[:50]}...")
    voice_utils.send_notification("Completion", completion)

def handle_record_menu(signum, frame):
    """Handle signal to show transcription."""
    global _stream, _audio, _wave_file, _recording
    log_utils.log_info("Received signal to show transcription")
    
    with _lock:
        _recording = False
        # Stop recording
        if _stream is not None:
            log_utils.log_info("Stopping recording")
            _stream.stop_stream()
            _stream.close()
            _stream = None
        
        if _audio is not None:
            _audio.terminate()
            _audio = None
        
        if _wave_file is not None:
            _wave_file.close()
            _wave_file = None
    
    # Save the recorded audio
    save_audio()
    
    # Transcribe the audio
    text = voice_utils.transcribe_audio()
    if not text:
        log_utils.log_error("No transcription available")
        return
    
    # Copy to clipboard and notify
    voice_utils.set_clipboard(text)
    log_utils.log_info(f"Transcription copied to clipboard: {text[:50]}...")
    voice_utils.send_notification("Transcription", text)

def handle_edit_menu(signum, frame):
    """Handle signal to stop recording and process edit."""
    global _stream, _audio, _wave_file, _recording
    log_utils.log_info("Received signal to stop recording for edit")
    
    with _lock:
        _recording = False
        # Stop recording
        if _stream is not None:
            log_utils.log_info("Stopping recording")
            _stream.stop_stream()
            _stream.close()
            _stream = None
        
        if _audio is not None:
            _audio.terminate()
            _audio = None
        
        if _wave_file is not None:
            _wave_file.close()
            _wave_file = None
    
    # Save the recorded audio
    save_audio()
    
    # Transcribe the audio
    text = voice_utils.transcribe_audio()
    if not text:
        log_utils.log_error("No transcription available")
        return
    
    # Get completion from OpenAI
    completion = voice_utils.get_completion(text, mode="edit")
    if not completion:
        log_utils.log_error("Failed to get completion from OpenAI")
        return
    
    # Copy completion to clipboard and notify
    voice_utils.set_clipboard(completion)
    log_utils.log_info(f"Edited text copied to clipboard: {completion[:50]}...")
    voice_utils.send_notification("Edit Complete", completion)

def setup_signal_handlers():
    """Set up signal handlers for the recording process."""
    signal.signal(signal.SIGUSR1, handle_completion_menu)  # Stop recording signal
    signal.signal(signal.SIGUSR2, handle_edit_menu)     # Stop recording for edit signal
    signal.signal(signal.SIGINT, handle_record_menu)    # Show transcription signal

def record_audio() -> None:
    """Record audio until interrupted."""
    global _stream, _audio, _wave_file, _recording
    
    CHUNK: int = 1024
    FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = 16000

    log_utils.log_info("Starting audio recording")
    _audio = pyaudio.PyAudio()
    _stream = _audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    # Open raw audio file for writing
    _wave_file = wave.open(RAW_AUDIO_FILE, 'wb')
    _wave_file.setnchannels(CHANNELS)
    _wave_file.setsampwidth(_audio.get_sample_size(FORMAT))
    _wave_file.setframerate(RATE)

    _recording = True
    try:
        while _recording:
            with _lock:
                if _stream is not None and _wave_file is not None:
                    if _stream.get_read_available() > 0:
                        data = _stream.read(_stream.get_read_available(), exception_on_overflow=False)
                        _wave_file.writeframes(data)
            time.sleep(0.1)
    except KeyboardInterrupt:
        log_utils.log_info("Recording interrupted by user")
    finally:
        with _lock:
            if _stream is not None:
                _stream.stop_stream()
                _stream.close()
                _stream = None
            
            if _audio is not None:
                _audio.terminate()
                _audio = None
            
            if _wave_file is not None:
                _wave_file.close()
                _wave_file = None
            
        log_utils.log_info("Recording stopped")

def save_audio() -> None:
    """Save recorded audio to the final file."""
    if not os.path.exists(RAW_AUDIO_FILE):
        log_utils.log_error("No raw audio file found")
        return

    log_utils.log_info(f"Copying raw audio to {AUDIO_FILE_NAME}")
    # Copy the raw audio file to the final location
    with open(RAW_AUDIO_FILE, 'rb') as src, open(AUDIO_FILE_NAME, 'wb') as dst:
        dst.write(src.read())
    
    # Clean up raw audio file
    os.remove(RAW_AUDIO_FILE)
    log_utils.log_info("Audio saved successfully")

def is_recording() -> bool:
    """Check if a recording is in progress."""
    pid = voice_utils.get_recording_pid()
    if pid is None:
        log_utils.log_debug("No recording PID file found")
        return False
    
    # Check if the process is still running
    try:
        os.kill(pid, 0)  # This will raise ProcessLookupError if the process is not running
        log_utils.log_debug(f"Recording in progress with PID {pid}")
        return True
    except ProcessLookupError:
        # Clean up stale PID file
        if os.path.exists(voice_utils.PID_FILE):
            log_utils.log_warning(f"Found stale PID file for process {pid}, removing")
            os.remove(voice_utils.PID_FILE)
        return False

def send_signal_to_recording(signal_type: int) -> None:
    """Send a signal to the recording process."""
    pid = voice_utils.get_recording_pid()
    if pid is not None:
        try:
            os.kill(pid, signal_type)
            log_utils.log_info(f"Sent signal {signal_type} to process {pid}")
        except ProcessLookupError:
            log_utils.log_error(f"Process {pid} not found")
    else:
        log_utils.log_warning("No recording process found")

def set_menu(menu: tk.Menu, root: tk.Tk) -> None:
    """Set the global menu instance."""
    # This function is no longer needed as we're using menu_utils
    pass 