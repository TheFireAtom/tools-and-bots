import os
import subprocess
import webbrowser
import requests
from dotenv import load_dotenv
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import openwakeword
from openwakeword.model import Model
import collections
#print(openwakeword.MODELS_DIR)  # или похожий атрибут, показывающий путь к моделям

load_dotenv()

API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")

if not os.path.exists("путь_к_папке_с_моделями"):
    openwakeword.utils.download_models()

# openwakeword.utils.download_models()  # закомментировано — модели уже скачаны
owwModel = Model(wakeword_models=["hey_jarvis"])

def open_explorer():
    subprocess.Popen("explorer.exe")


def open_task_manager():
    subprocess.Popen("taskmgr.exe")


def open_notepad():
    subprocess.Popen("notepad.exe")

openwakeword.utils.download_models()  # скачивает предобученные модели один раз

owwModel = Model(wakeword_models=["hey_jarvis"])  # встроенная готовая модель под "Hey Jarvis"

def listen_for_wake_word():
    print("Жду слово 'Jarvis'...")
    samplerate = 16000
    chunk_size = int(0.25 * samplerate)  # четверть секунды за раз, чаще проверяем
    buffer = collections.deque(maxlen=samplerate * 2)  # держим последние 2 секунды звука
    
    while True:
        chunk = sd.rec(chunk_size, samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        buffer.extend(chunk.flatten())
        
        audio_window = np.array(buffer)
        prediction = owwModel.predict(audio_window)
        
        for wakeword, score in prediction.items():
            if score > 0.4:
                print("Джарвис активирован!")
                return True

def web_search(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

def ask_gpt_with_fallback(user_text):
    answer = ask_gpt(user_text)
    
    uncertain_phrases = ["не знаю", "у меня нет информации", "не могу ответить", "не уверен"]
    
    if any(phrase in answer.lower() for phrase in uncertain_phrases):
        print("GPT не уверен, ищу в интернете...")
        web_search(user_text)
        return f"Не уверен в ответе, поэтому ищу '{user_text}' в браузере для тебя"
    
    return answer

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
        "lang": "ru-RU",
        "format": "lpcm",
        "sampleRateHertz": "16000"
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
        return ask_gpt_with_fallback(user_text)

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

def jarvis_full_loop():
    print("Альфред к вашим услугам, сэр.")
    while True:
        try:
            listen_for_wake_word()
            record_audio(duration=5)
            command_text = speech_to_text()
            print(f"Ты сказал: {command_text}")
            
            if "выход" in command_text.lower():
                break
            
            answer = handle_command(command_text)
            print(f"Джарвис: {answer}")
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            continue  # не роняем программу, просто пробуем заново

if __name__ == "__main__":
    jarvis_full_loop()