#!/usr/bin/env python3

"""OpenAI API utilities: transcription and chat completion."""

from pathlib import Path
from typing import Optional

from openai import OpenAI

import config
from utils import log

# OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)


def transcribe_audio(audio_file) -> Optional[str]:
    """Transcribe the audio data and return the text.

    Args:
        audio_file: A file-like object or path to the audio file

    Returns:
        Transcribed text if successful, None otherwise
    """
    log.log_info("Starting audio transcription")
    try:
        if isinstance(audio_file, str):
            audio_file = Path(audio_file)

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        text = transcript.text
        log.log_info(f"Transcription successful: {text[:50]}...")
        return text
    except Exception as e:
        log.log_error(f"Error transcribing audio: {e}")
        return None


def get_completion(text: str) -> Optional[str]:
    """Send text to OpenAI for completion and return the response.

    Args:
        text: The user prompt or voice directive

    Returns:
        Completion text if successful, None otherwise
    """
    log.log_info("Sending text to OpenAI for completion")
    try:
        system_prompt = """You are an AI system designed to process dictated directives and generate concise text responses suitable for clipboard use. Your functionalities include:

1. Accepting voice or text directives from users.
2. Generating brief, clear, and relevant text based on the directive suitable for being put into the user's clipboard.
3. Ensuring the output is suitable for immediate use in various applications (e.g., emails, documents).
4. Maintaining a direct and efficient communication style without unnecessary filler or politeness."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        completion = response.choices[0].message.content
        log.log_info(f"Completion successful: {completion[:50]}...")
        return completion
    except Exception as e:
        log.log_error(f"Error getting completion: {e}")
        return None


def get_edit(directive: str, get_clipboard) -> Optional[str]:
    """Edit clipboard content based on a voice directive and return the result.

    Args:
        directive: The voice directive describing what changes to make
        get_clipboard: Function to get the current clipboard content

    Returns:
        Edited text if successful, None otherwise
    """
    log.log_info("Sending text to OpenAI for edit")
    try:
        clipboard_text = get_clipboard()
        if not clipboard_text:
            log.log_error("No clipboard content available")
            return None

        system_prompt = """You are an AI system designed to perform surgical edits on text based on voice directives. Your task is to:

1. Take the provided original_text in full
2. Use the voice_directive to understand what specific changes are requested
3. Apply ONLY the requested changes—leave all other text exactly as it appears in the original
4. Output the COMPLETE text: the full original with only the specified parts modified. Do not output just the edited snippet or the changed portion. The response must be the entire document, with surgical edits applied where indicated.
5. Maintain the original style and tone
6. Respond with only the full edited text, without explanations or commentary"""

        user_prompt = f"<original_text>{clipboard_text}</original_text>\n<voice_directive>{directive}</voice_directive>"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        completion = response.choices[0].message.content
        log.log_info(f"Edit successful: {completion[:50]}...")
        return completion
    except Exception as e:
        log.log_error(f"Error getting edit: {e}")
        return None
