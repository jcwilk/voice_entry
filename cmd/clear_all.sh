#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Kill all processes related to voice_entry
echo "Killing all voice_entry processes..."
pkill -f "voice_entry/cmd"
pkill -f "python.*voice_entry.py"

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -f /tmp/voice_entry_audio.wav
rm -f /tmp/voice_entry.pid
rm -f /tmp/voice_entry_text.txt
rm -f /tmp/voice_entry_raw.wav

echo "Cleanup complete!" 