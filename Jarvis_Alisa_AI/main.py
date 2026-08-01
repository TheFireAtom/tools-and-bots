import os
import subprocess
import webbrowser
import requests
from dotenv import load_dotenv
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

load_dotenv()

API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")

def open_explorer():
    subprocess.Popen("explorer.exe")


def open_task_manager():
    subprocess.Popen("taskmgr.exe")


def open_notepad():
    subprocess.Popen("notepad.exe")


def web_search(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

def record_audio(filename="input.wav", duration=5, samplerate=16000):
    print("Говори...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # ждём, пока запись закончится
    write(filename, samplerate, audio)
    print("Запись окончена")


def speech_to_text(filename="input.wav"):
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    headers = {
        "Authorization": f"Api-Key {API_KEY}"
    }

    params = {
        "folderId": FOLDER_ID,
        "lang": "ru-RU"
    }

    with open(filename, "rb") as f:
        audio_data = f.read()

    response = requests.post(url, headers=headers, params=params, data=audio_data)
    result = response.json()
    print("STT ответ:", result)  # временно
    return result.get("result", "")

def handle_command(user_text):
    text = user_text.lower()

    if "проводник" in text:
        open_explorer()
        return "Открываю проводник"
    elif "диспетчер задач" in text:
        open_task_manager()
        return "Открываю диспетчер задач"
    elif "блокнот" in text:
        open_notepad()
        return "Открываю блокнот"
    elif "найди" in text or "поищи" in text:
        query = text.replace("найди", "").replace("поищи", "").strip()
        web_search(query)
        return f"Ищу: {query}"
    else:
        return ask_gpt(user_text)

def jarvis_voice_loop():
    print("Джарвис (голосовой режим). Скажи 'выход', чтобы закончить.")
    while True:
        record_audio()
        user_text = speech_to_text()
        print(f"Ты сказал: {user_text}")

        if "выход" in user_text.lower():
            break

        answer = handle_command(user_text)
        print(f"Джарвис: {answer}")

def ask_gpt(user_text, system_prompt="Ты дружелюбный ассистент по имени Джарвис."):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}",
        "x-folder-id": FOLDER_ID
    }

    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 500
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_text}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    print(result)  # временно, чтобы увидеть ошибку
    return result["result"]["alternatives"][0]["message"]["text"]

# def jarvis_loop():
#     print("Джарвис запущен. Напиши 'выход', чтобы закончить.")
#     while True:
#         user_input = input("Ты: ")
#         if user_input.lower() == "выход":
#             break

#         answer = handle_command(user_input)
#         print(f"Джарвис: {answer}")


if __name__ == "__main__":
    jarvis_voice_loop()