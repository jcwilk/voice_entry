import openai
import os
from gi.repository import Notify
import subprocess
import pyaudio
import wave
import time
import audioop
import config

openai.api_key = config.OPENAI_API_KEY

PAUSE_TIME_GRACE_PERIOD = 2  # Adjust this value to change the grace period

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

def save_audio_input(file_name):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    SILENCE_THRESHOLD = 300  # Adjust this value to change the silence threshold

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print_and_notify("Info", "Please say something...")

    frames = []
    last_non_silent_time = time.time()

    while time.time() - last_non_silent_time < PAUSE_TIME_GRACE_PERIOD:
        data = stream.read(CHUNK)
        rms = audioop.rms(data, 2)
        if rms > SILENCE_THRESHOLD:
            last_non_silent_time = time.time()
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def get_audio_input():
    file_name = "audio.wav"
    save_audio_input(file_name)

    try:
        with open(file_name, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        print_and_notify("You said:", text)
        response = send_text_to_openai_api(text)
        print_and_notify("OpenAI API Response:", response)
        set_clipboard(response)
    except Exception as e:
        print_and_notify("Error", f"Could not request results from OpenAI Speech to Text service; {e}")

def send_text_to_openai_api(text):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                { "role": "system", "content": "You are a code generator. The user will dictate a request describing the generation of some code-like text. The dictation will be transcribed and provided as user input. There may be incorrect homonyms or other similar transcription errors. Your response should contain ONLY the requested output, NO surrounding triple-ticks or explanations unless they are EXPLICITLY asked for." },
                { "role": "user", "content": f"""
Transcribed request:
```
{text}
```"""
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        response = completion['choices'][0]['message']['content']
        return response.strip()
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    get_audio_input()
