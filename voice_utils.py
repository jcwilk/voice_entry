#!/usr/bin/env python3

import os
import tempfile
import subprocess
from typing import Optional
import signal
from openai import OpenAI
import config
import time
import log_utils
import gi
from pathlib import Path
gi.require_version('Notify', '0.7')
from gi.repository import Notify

# File paths
AUDIO_FILE_NAME: str = os.path.join(tempfile.gettempdir(), "voice_entry_audio.wav")
PID_FILE: str = os.path.join(tempfile.gettempdir(), "voice_entry.pid")

# OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)

def send_notification(title: str, text: str) -> None:
    """Send a desktop notification."""
    Notify.init("Voice Entry")
    notification = Notify.Notification.new(title, text, None)
    notification.show()

def set_clipboard(text: str) -> None:
    """Copy text to clipboard."""
    log_utils.log_info(f"Copying to clipboard: {text[:50]}...")
    process = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

def get_recording_pid() -> Optional[int]:
    """Get the PID of the currently running recording process."""
    if not os.path.exists(PID_FILE):
        log_utils.log_debug("No PID file found")
        return None
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
            log_utils.log_debug(f"Found PID file with PID: {pid}")
            return pid
    except (ValueError, FileNotFoundError) as e:
        log_utils.log_error(f"Error reading PID file: {e}")
        return None

def transcribe_audio() -> Optional[str]:
    """Transcribe the audio file and return the text."""
    log_utils.log_info("Starting audio transcription")
    try:
        # Use pathlib to handle the file
        audio_path = Path(AUDIO_FILE_NAME)
        if not audio_path.exists():
            log_utils.log_error("Audio file does not exist")
            return None
            
        if audio_path.stat().st_size == 0:
            log_utils.log_error("Audio file is empty")
            return None
            
        # Read the entire file into memory
        audio_data = audio_path.read_bytes()
        
        # Create a file-like object from the bytes
        from io import BytesIO
        audio_file = BytesIO(audio_data)
        audio_file.name = "audio.wav"  # Set a name for the file-like object
        
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        text = transcript.text
        log_utils.log_info(f"Transcription successful: {text[:50]}...")
        return text
    except Exception as e:
        log_utils.log_error(f"Error transcribing audio: {e}")
        return None

def get_clipboard() -> Optional[str]:
    """Get text from clipboard."""
    try:
        process = subprocess.Popen(['xclip', '-selection', 'c', '-o'], stdout=subprocess.PIPE)
        output, _ = process.communicate()
        return output.decode('utf-8').strip()
    except Exception as e:
        log_utils.log_error(f"Error reading clipboard: {e}")
        return None

def get_completion(text: str, mode: str = "context") -> Optional[str]:
    """Send text to OpenAI for completion and return the response."""
    log_utils.log_info(f"Sending text to OpenAI for {mode} completion")
    try:
        if mode == "edit":
            clipboard_text = get_clipboard()
            if not clipboard_text:
                log_utils.log_error("No clipboard content available")
                return None
            
            system_prompt = """You are an AI system designed to edit text based on voice directives. Your task is to:
1. Take the provided text from the clipboard
2. Use the voice directive to understand what changes are needed
3. Generate an edited version of the text that incorporates the requested changes
4. Maintain the original style and tone while making the requested modifications
5. Return only the edited text, without explanations or commentary"""
            
            user_prompt = f"Original text:\n{clipboard_text}\n\nVoice directive for editing:\n{text}"
        else:
            system_prompt = """You are an AI system designed to process dictated directives and generate concise text responses suitable for clipboard use. Your functionalities include:

1. Accepting voice or text directives from users.
2. Generating brief, clear, and relevant text based on the directive suitable for being put into the user's clipboard.
3. Ensuring the output is suitable for immediate use in various applications (e.g., emails, documents).
4. Maintaining a direct and efficient communication style without unnecessary filler or politeness."""
            
            user_prompt = text

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        completion = response.choices[0].message.content
        log_utils.log_info(f"Completion successful: {completion[:50]}...")
        return completion
    except Exception as e:
        log_utils.log_error(f"Error getting completion: {e}")
        return None

def type_text(text: str) -> None:
    """Type out text at the current cursor position.
    
    Args:
        text: The text to type out
    """
    try:
        # Use xdotool to type the text
        subprocess.run(['xdotool', 'type', '--clearmodifiers', text], check=True)
    except subprocess.CalledProcessError as e:
        log_utils.log_error(f"Failed to type text: {e}")
    except FileNotFoundError:
        log_utils.log_error("xdotool not found. Please install it to use the type functionality.") 