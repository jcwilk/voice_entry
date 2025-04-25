# Voice Entry

A voice-to-text tool that allows you to record audio and process it in various ways.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/voice_entry.git
cd voice_entry
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install system dependencies:
```bash
sudo apt-get install xclip xdotool
```

5. Set up your OpenAI API key:
```bash
cp config.example.py config.py
# Edit config.py and add your OpenAI API key
```

## Usage

The tool provides several commands for different operations:

### Recording

Start recording audio:
```bash
cmd/record.sh
```

While recording is in progress, you can use the following commands:

### Transcription

Get the raw transcription of your recording:
```bash
cmd/record.sh
```
This will stop the recording and show the transcription.

### Completion

Get an AI-generated completion based on your recording:
```bash
cmd/completion.sh
```
This will process your recording through GPT-3.5 and provide a completion.

### Edit

Edit the current clipboard content based on your recording:
```bash
cmd/edit.sh
```
This will use your recording as instructions to edit the text in your clipboard.

### Type

Type out the transcription at the current cursor position:
```bash
cmd/type.sh
```
This will type out the transcription directly where your cursor is.

## How It Works

1. Start recording with `cmd/record.sh`
2. While recording, use any of the other commands to process the audio
3. The tool will:
   - Stop recording
   - Transcribe the audio
   - Process it according to the command used
   - Either copy to clipboard, type out, or show the result

## Requirements

- Python 3.8+
- OpenAI API key
- xclip (for clipboard operations)
- xdotool (for typing functionality)
- ALSA (for audio recording)

## License

MIT 