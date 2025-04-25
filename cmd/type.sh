#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/../venv/bin/activate"

# Run the type command
python "$SCRIPT_DIR/../voice_entry.py" type 