import openai
import os
import pyaudio
import wave
from gi.repository import Notify
import subprocess
import time

openai.api_key = "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"
FLAG_FILE_NAME = "recording_flag.txt"
AUDIO_FILE_NAME = "audio.wav"

def set_clipboard(text):
    process = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

def send_notification(title, text):
    Notify.init("Voice Input")
    notification = Notify.Notification.new(title, text, None)
    notification.show()

def print_and_notify(title, text):
    print(title, text)
    send_notification(title, text)

def start_recording():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print_and_notify("Info", "Please say something...")

    frames = []

    while os.path.isfile(FLAG_FILE_NAME):
        frames.append(stream.read(CHUNK))
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(AUDIO_FILE_NAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    get_audio_input()

def stop_recording():
    if os.path.isfile(FLAG_FILE_NAME):
        os.remove(FLAG_FILE_NAME)

def get_audio_input():
    try:
        with open(AUDIO_FILE_NAME, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        print_and_notify("You said:", text)
        set_clipboard(text)
    except Exception as e:
        print_and_notify("Error", f"Could not request results from OpenAI Speech to Text service; {e}")

def main():
    if os.path.isfile(FLAG_FILE_NAME):
        stop_recording()
    else:
        with open(FLAG_FILE_NAME, 'w') as f:
            pass
        start_recording()

if __name__ == "__main__":
    main()
