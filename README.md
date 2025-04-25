# Voice Entry

A voice recording and transcription tool that uses OpenAI's Whisper API.

## Setup

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip portaudio19-dev libnotify-dev
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `config.py` file with your OpenAI API key:
```python
OPENAI_API_KEY = "your-api-key-here"
```

## Usage

1. Start recording:
```bash
./cmd/record.sh
```

2. Stop recording and get transcription:
```bash
./cmd/record.sh
```

3. Get completion from transcription:
```bash
./cmd/completion.sh
```

4. Edit clipboard contents based on transcription:
```bash
./cmd/edit.sh
```

5. Clean up all processes and temporary files:
```bash
./cmd/clear_all.sh
```

## Features

- Voice recording with automatic transcription
- OpenAI Whisper API integration
- Desktop notifications
- Clipboard integration
- Process management
- Temporary file cleanup 