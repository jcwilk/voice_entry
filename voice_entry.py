#!/usr/bin/env python3

from openai import OpenAI
import os
import pyaudio
import wave
from gi.repository import Notify
import subprocess
import time
import config
import signal
import sys
import tempfile
from typing import List, Optional, Tuple

client = OpenAI(
    api_key=config.OPENAI_API_KEY,
)

AUDIO_FILE_NAME: str = os.path.join(tempfile.gettempdir(), "voice_entry_audio.wav")
PID_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry.pid")

def set_clipboard(text: str) -> None:
    process = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

def send_notification(title: str, text: str) -> None:
    Notify.init("Voice Input")
    notification = Notify.Notification.new(title, text, None)
    notification.show()

def print_and_notify(title: str, text: str) -> None:
    print(title, text)
    send_notification(title, text)

def record_audio() -> List[bytes]:
    CHUNK: int = 1024
    FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames: List[bytes] = []

    print_and_notify("Info", "Recording... Press Ctrl+C to stop.")

    try:
        while True:
            if stream.get_read_available() > 0:
                data = stream.read(stream.get_read_available(), exception_on_overflow=False)
                frames.append(data)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    return frames

def save_audio(frames: List[bytes]) -> None:
    wf = wave.open(AUDIO_FILE_NAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit audio
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

def process_audio() -> None:
    try:
        with open(AUDIO_FILE_NAME, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        text = transcript.text
        print_and_notify("You said:", text)
        set_clipboard(text)
    except Exception as e:
        print_and_notify("Error", f"Could not request results from OpenAI Speech to Text service; {e}")

def get_recording_pid() -> Optional[int]:
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except (ValueError, FileNotFoundError):
        return None

def stop_recording(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGINT)
        os.remove(PID_FILE)
    except ProcessLookupError:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def main() -> None:
    pid = get_recording_pid()
    
    if pid is not None:
        # Stop existing recording
        stop_recording(pid)
    else:
        # Start new recording
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            frames = record_audio()
            save_audio(frames)
            process_audio()
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

if __name__ == "__main__":
    main()
