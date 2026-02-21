#!/usr/bin/env python3

"""Send queries to Perplexity SonarPro API - used when feeding from recording or clipboard."""

from openai import OpenAI

import config
from utils import log
from utils import notification
from utils import voice


def run_perplexity(text: str) -> None:
    """Send text to Perplexity SonarPro and put the response on the clipboard.

    Uses the Perplexity API (OpenAI-compatible) with the sonar-pro model.
    Copies the response to clipboard and shows a notification.

    Args:
        text: The query text to send (from transcription or clipboard).
    """
    if not text or not text.strip():
        log.log_warning("Empty text for Perplexity, skipping")
        return

    if not config.PERPLEXITY_API_KEY:
        log.log_error("PERPLEXITY_API_KEY not set in config.py")
        notification.send_notification("Perplexity", "API key not configured")
        return

    log.log_info(f"Running Perplexity with: {text[:80]}...")

    try:
        client = OpenAI(
            api_key=config.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": "Be concise and helpful. Provide direct answers suitable for clipboard use. Use plain text only—no formatting, no markdown, no asterisks, no bold or italics, no bullet points or numbered lists. Output should be minimal and unformatted."},
                {"role": "user", "content": text.strip()}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        result = response.choices[0].message.content
        if result:
            voice.set_clipboard(result)
            log.log_info(f"Copied to clipboard: {result[:50]}...")
            notification.send_notification("Perplexity", result)
        else:
            log.log_warning("Empty response from Perplexity")
            notification.send_notification("Perplexity", "No response received")
    except Exception as e:
        log.log_error(f"Failed to run Perplexity: {e}")
        notification.send_notification("Perplexity", f"Error: {e}")
