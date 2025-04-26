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
sudo apt-get install xclip xdotool libnotify-bin
```

5. Set up your OpenAI API key:
```bash
cp config.example.py config.py
# Edit config.py and add your OpenAI API key
```

## Usage

The tool provides several commands for different operations, all located in the `cmd` directory. For the best experience, it's recommended to set up system-level hotkeys to trigger these commands from anywhere in your system.

### Setting Up Hotkeys

You can set up hotkeys in your desktop environment's keyboard shortcuts settings. For example, in GNOME:
1. Go to Settings > Keyboard > Keyboard Shortcuts
2. Add custom shortcuts for each command:
   - `cmd/record.sh` - Start/stop recording (recommended: alt+shift+c)
   - `cmd/completion.sh` - Get completion (recommended: alt+shift+v)
   - `cmd/edit.sh` - Edit clipboard content (recommended: alt+shift+x)
   - `cmd/type.sh` - Type out transcription (recommended: alt+shift+d)

### Recording

Start recording audio:
```bash
cmd/record.sh
```
This will start recording your voice. While recording is in progress, you can use any of the other commands to process the audio.

### Transcription

Get the raw transcription of your recording:
```bash
cmd/record.sh
```
This will stop the current recording and show the transcription in a notification.

### Completion

Get an AI-generated completion based on your recording or clipboard:
```bash
cmd/completion.sh
```
This command works in two ways:
- If a recording is in progress, it will stop the recording, transcribe it, and generate a completion based on the transcription
- If no recording is in progress, it will take the text from your clipboard, generate a completion, and copy the result back to your clipboard

### Edit

Edit the current clipboard content based on your recording:
```bash
cmd/edit.sh
```
This will:
- Stop the current recording
- Transcribe the audio
- Use the transcription as instructions to edit the text in your clipboard
- Copy the edited text back to your clipboard

### Type

Type out the transcription at the current cursor position:
```bash
cmd/type.sh
```
This will:
- Stop the current recording
- Transcribe the audio
- Type out the transcription directly where your cursor is without affecting your clipboard

### Cleanup

If you need to stop all voice entry processes and clean up temporary files:
```bash
cmd/clear_all.sh
```

## Requirements

- Python 3.8+
- OpenAI API key
- xclip (for clipboard operations)
- xdotool (for typing functionality)
- libnotify-bin (for desktop notifications)
- ALSA (for audio recording)

## License

MIT 