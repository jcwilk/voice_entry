import openai
import os
from gi.repository import Notify
import subprocess
import pyaudio
import wave
import time
import audioop

openai.api_key = "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"

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
        prompt_template = (
            "Given the following request:\n"
            "```\n"
            "{task_description}\n"
            "```\n"
            "Omitting any \"```\" formatting marks, the code to satisfy the ask follows the colon:\n"
        )

        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt_template.format(task_description=text),
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5,
            top_p=1
        )
        response = completion.choices[0].text
        return response.strip()
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    get_audio_input()
