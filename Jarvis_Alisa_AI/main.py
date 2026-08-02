import os
import subprocess
import webbrowser
import requests
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from dotenv import load_dotenv
import openwakeword
from openwakeword.model import Model
from win11toast import notify
import pygame

load_dotenv()

API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")

# openwakeword.utils.download_models()  # раскомментируй при первом запуске
owwModel = Model(wakeword_models=["hey_jarvis"])

pygame.mixer.init()


# ---------- Запись и распознавание речи ----------

def record_audio(filename="input.wav", duration=5, samplerate=16000):
    print("Говори...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, audio)
    print("Запись окончена")


def speech_to_text(filename="input.wav"):
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {"Authorization": f"Api-Key {API_KEY}"}
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
    return result.get("result", "")


# ---------- Wake word ----------

def listen_for_wake_word():
    print("Жду слово 'Jarvis'...")
    samplerate = 16000
    chunk_duration = 1

    while True:
        audio_chunk = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        audio_chunk = audio_chunk.flatten()

        prediction = owwModel.predict(audio_chunk)

        for wakeword, score in prediction.items():
            if score > 0.4:
                print("Джарвис активирован!")
                return True


# ---------- Веб-поиск (DuckDuckGo) ----------

def perform_actual_search(query):
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1}
    response = requests.get(url, params=params)
    data = response.json()

    abstract = data.get("AbstractText", "")
    if abstract:
        return abstract

    related = data.get("RelatedTopics", [])
    if related:
        return related[0].get("Text", "Информация не найдена")

    return "Информация не найдена"


# ---------- GPT с function calling ----------

def ask_gpt_with_tools(user_text, system_prompt="Ты дружелюбный ассистент по имени Джарвис."):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}",
        "x-folder-id": FOLDER_ID
    }

    tools = [
        {
            "function": {
                "name": "web_search",
                "description": "Ищет информацию в интернете, когда у ассистента нет собственных знаний по теме или нужны свежие данные",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "text": system_prompt},
        {"role": "user", "text": user_text}
    ]

    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/rc",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 500},
        "messages": messages,
        "tools": tools
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    alternative = result["result"]["alternatives"][0]

    if "toolCallList" in alternative.get("message", {}):
        tool_calls = alternative["message"]["toolCallList"]["toolCalls"]
        messages.append(alternative["message"])

        for call in tool_calls:
            if call["functionCall"]["name"] == "web_search":
                query = call["functionCall"]["arguments"]["query"]
                search_result = perform_actual_search(query)

                messages.append({
                    "role": "assistant",
                    "toolResultList": {
                        "toolResults": [
                            {"functionResult": {"name": "web_search", "content": search_result}}
                        ]
                    }
                })

        payload["messages"] = messages
        final_response = requests.post(url, headers=headers, json=payload)
        final_result = final_response.json()
        return final_result["result"]["alternatives"][0]["message"]["text"]

    return alternative["message"]["text"]


# ---------- Синтез речи (TTS) ----------

def text_to_speech(text, output_file="response.ogg"):
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    headers = {"Authorization": f"Api-Key {API_KEY}"}
    data = {
        "text": text,
        "lang": "ru-RU",
        "voice": "jane",
        "folderId": FOLDER_ID
    }
    response = requests.post(url, headers=headers, data=data)
    with open(output_file, "wb") as f:
        f.write(response.content)


def play_audio(filename="response.ogg"):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


# ---------- Уведомления ----------

def show_notification(title, message):
    notify(title, message, duration="short")


# ---------- Системные команды ----------

def open_explorer():
    subprocess.Popen("explorer.exe")


def open_task_manager():
    subprocess.Popen("taskmgr.exe")


def open_notepad():
    subprocess.Popen("notepad.exe")


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
    else:
        return ask_gpt_with_tools(user_text)


# ---------- Ответ пользователю (уведомление + голос) ----------

def respond(answer):
    print(f"Джарвис: {answer}")
    show_notification("Джарвис", answer)
    text_to_speech(answer)
    play_audio()


# ---------- Основной цикл ----------

def jarvis_full_loop():
    print("Джарвис запущен в фоновом режиме.")
    while True:
        try:
            listen_for_wake_word()
            record_audio(duration=5)
            command_text = speech_to_text()
            print(f"Ты сказал: {command_text}")

            if "выход" in command_text.lower():
                break

            answer = handle_command(command_text)
            respond(answer)
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            continue


if __name__ == "__main__":
    jarvis_full_loop()