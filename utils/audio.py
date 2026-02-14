#!/usr/bin/env python3

import os
import pyaudio
import wave
import time
from typing import List, Optional, NamedTuple
from utils import voice
from utils import log
from utils import notification
from utils import typing
import threading
import tempfile
import signal
from io import BytesIO

# File paths
AUDIO_FILE_NAME: str = os.path.join(tempfile.gettempdir(), "voice_entry_audio.wav")
PID_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry.pid")
TEXT_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry_text.txt")

class AudioState(NamedTuple):
    stream: Optional[pyaudio.Stream] = None
    audio: Optional[pyaudio.PyAudio] = None
    wave_file: Optional[wave.Wave_write] = None
    recording: bool = False

_lock = threading.Lock()

def process_audio_and_notify(operation: str, process_func, state: AudioState, should_type: bool = False) -> None:
    """Process recorded audio and notify with the result.
    
    Args:
        operation: Name of the operation (e.g. "Completion", "Edit", "Transcription")
        process_func: Function to process the transcription text
        state: Current audio recording state
        should_type: Whether to type out the result instead of copying to clipboard
    """
    log.log_info(f"Processing audio for {operation}")
    
    # Stop recording and clean up
    with _lock:
        if state.stream is not None:
            state.stream.stop_stream()
            state.stream.close()
        
        if state.audio is not None:
            state.audio.terminate()
        
        if state.wave_file is not None:
            # Ensure all data is written and file is properly closed
            state.wave_file.flush()
            state.wave_file.close()
            # Force sync to disk
            os.fsync(os.open(AUDIO_FILE_NAME, os.O_RDONLY))
    
    # Transcribe the audio
    text = voice.transcribe_audio(AUDIO_FILE_NAME)
    if not text:
        log.log_error("No transcription available")
        os._exit(0)  # Exit the process
        return
    
    # Process the text using the provided function
    result = process_func(text)
    if not result:
        log.log_error(f"Failed to process text for {operation}")
        os._exit(0)  # Exit the process
        return
    
    if should_type:
        typing.type_out(result, operation)
    else:
        # Copy result to clipboard and notify
        voice.set_clipboard(result)
        log.log_info(f"{operation} copied to clipboard: {result[:50]}...")
        notification.send_notification(operation, result)
    
    # Exit the process after handling the signal
    os._exit(0)

def record_audio(state: AudioState) -> AudioState:
    """Record audio until interrupted.
    
    Args:
        state: Initial audio state
        
    Returns:
        Updated audio state
    """
    CHUNK: int = 1024
    FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = 16000

    log.log_info("Starting audio recording")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    # Open audio file for writing
    wave_file = wave.open(AUDIO_FILE_NAME, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(audio.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)

    new_state = AudioState(stream=stream, audio=audio, wave_file=wave_file, recording=True)
    
    try:
        while new_state.recording:
            with _lock:
                if new_state.stream is not None and new_state.wave_file is not None:
                    if new_state.stream.get_read_available() > 0:
                        data = new_state.stream.read(new_state.stream.get_read_available(), exception_on_overflow=False)
                        new_state.wave_file.writeframes(data)
            time.sleep(0.1)
    finally:
        with _lock:
            # One final read to capture any remaining audio in the buffer
            if new_state.stream is not None and new_state.wave_file is not None:
                if new_state.stream.get_read_available() > 0:
                    data = new_state.stream.read(new_state.stream.get_read_available(), exception_on_overflow=False)
                    new_state.wave_file.writeframes(data)
            
            if new_state.stream is not None:
                new_state.stream.stop_stream()
                new_state.stream.close()
            
            if new_state.audio is not None:
                new_state.audio.terminate()
            
            if new_state.wave_file is not None:
                new_state.wave_file.close()
            
        log.log_info("Recording stopped")
        return AudioState(recording=False)

def is_recording() -> bool:
    """Check if a recording is in progress."""
    pid = voice.get_recording_pid()
    if pid is None:
        log.log_debug("No recording PID file found")
        return False
    
    # Check if the process is still running
    try:
        os.kill(pid, 0)  # This will raise ProcessLookupError if the process is not running
        log.log_debug(f"Recording in progress with PID {pid}")
        return True
    except ProcessLookupError:
        # Clean up stale PID file
        if os.path.exists(voice.PID_FILE):
            log.log_warning(f"Found stale PID file for process {pid}, removing")
            os.remove(voice.PID_FILE)
        return False

def send_signal_to_recording(signal_type: int) -> None:
    """Send a signal to the recording process."""
    pid = voice.get_recording_pid()
    if pid is not None:
        try:
            os.kill(pid, signal_type)
            log.log_info(f"Sent signal {signal_type} to process {pid}")
        except ProcessLookupError:
            log.log_error(f"Process {pid} not found")
    else:
        log.log_warning("No recording process found")
