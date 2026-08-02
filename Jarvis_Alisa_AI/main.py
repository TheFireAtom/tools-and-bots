import os
import re
import time
import subprocess
import threading
import tkinter as tk

import requests
import sounddevice as sd
import pygame
import pyautogui
import pyperclip
from scipy.io.wavfile import write
from dotenv import load_dotenv
import openwakeword
from openwakeword.model import Model

load_dotenv()

API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# openwakeword.utils.download_models()  # раскомментируй при первом запуске на новой машине
owwModel = Model(wakeword_models=["hey_jarvis"])

pygame.mixer.init()

NOTES_FILE = "notes.txt"
last_answer = ""
stop_flag = threading.Event()


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

def text_to_speech(text, output_file="response.mp3"):
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    headers = {"Authorization": f"Api-Key {API_KEY}"}
    data = {
        "text": text,
        "lang": "ru-RU",
        "voice": "ermil",
        "emotion": "neutral",
        "folderId": FOLDER_ID,
        "format": "mp3"
    }
    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("TTS ошибка:", response.text)
        return

    with open(output_file, "wb") as f:
        f.write(response.content)


def play_audio(filename="response.mp3"):
    stop_flag.clear()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    listener_thread = threading.Thread(target=listen_for_stop_command, daemon=True)
    listener_thread.start()

    while pygame.mixer.music.get_busy():
        if stop_flag.is_set():
            pygame.mixer.music.stop()
            print("Озвучка остановлена по команде")
            break
        pygame.time.Clock().tick(10)


def listen_for_stop_command():
    stop_words = ["стоп", "хватит", "перестань"]
    samplerate = 16000
    chunk_duration = 1.5

    while pygame.mixer.music.get_busy():
        audio_chunk = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()

        temp_filename = "stop_check.wav"
        write(temp_filename, samplerate, audio_chunk)
        text = speech_to_text(temp_filename).lower()

        if any(word in text for word in stop_words):
            stop_flag.set()
            return


# ---------- Текстовое окно ----------

def show_text_window(title, message, duration=6000):
    def _show():
        window = tk.Tk()
        window.title(title)
        window.attributes("-topmost", True)
        window.geometry("650x300+50+50")

        label = tk.Label(
            window,
            text=message,
            wraplength=620,
            justify="left",
            padx=15,
            pady=15,
            font=("Segoe UI", 16)
        )
        label.pack(expand=True, fill="both")

        window.after(duration, window.destroy)
        window.mainloop()

    threading.Thread(target=_show, daemon=True).start()


# ---------- Системные команды ----------

def open_explorer():
    subprocess.Popen("explorer.exe")


def open_task_manager():
    subprocess.Popen("taskmgr.exe")


def open_notepad():
    subprocess.Popen("notepad.exe")


# ---------- Таймеры ----------

def set_timer(minutes, label="Таймер"):
    def timer_thread():
        time.sleep(minutes * 60)
        message = f"{label}: время вышло!"
        respond(message)

    thread = threading.Thread(target=timer_thread, daemon=True)
    thread.start()
    return f"Таймер на {minutes} минут запущен"


# ---------- Заметки ----------

def add_note(note_text):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(note_text.strip() + "\n")
    return f"Записал: {note_text}"


def read_notes():
    if not os.path.exists(NOTES_FILE):
        return "Заметок пока нет"

    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        notes = f.readlines()

    if not notes:
        return "Заметок пока нет"

    return "Вот твои заметки: " + "; ".join(n.strip() for n in notes)


# ---------- Погода ----------

def get_weather(city="Moscow"):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "Не удалось получить данные о погоде"

    data = response.json()
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]

    return f"В Москве сейчас {temp:.0f} градусов, ощущается как {feels_like:.0f}, {description}"


# ---------- Управление музыкой ----------

def media_play_pause():
    pyautogui.press("playpause")
    return "Пауза/воспроизведение"


def media_next_track():
    pyautogui.press("nexttrack")
    return "Следующий трек"


def media_prev_track():
    pyautogui.press("prevtrack")
    return "Предыдущий трек"


# ---------- Буфер обмена ----------

def copy_last_answer():
    if last_answer:
        pyperclip.copy(last_answer)
        return "Скопировал последний ответ в буфер обмена"
    return "Пока нечего копировать"


# ---------- Обработка команд ----------

def handle_command(user_text):
    global last_answer
    text = user_text.lower()

    if "проводник" in text:
        open_explorer()
        answer = "Открываю проводник"

    elif "диспетчер задач" in text:
        open_task_manager()
        answer = "Открываю диспетчер задач"

    elif "блокнот" in text:
        open_notepad()
        answer = "Открываю блокнот"

    elif "таймер" in text:
        match = re.search(r'(\d+)', text)
        minutes = int(match.group(1)) if match else 5
        answer = set_timer(minutes)

    elif "запиши" in text or "заметка" in text:
        note_text = text.replace("запиши", "").replace("заметка", "").strip()
        answer = add_note(note_text)

    elif "прочитай заметки" in text or "список заметок" in text:
        answer = read_notes()

    elif "погода" in text:
        answer = get_weather()

    elif "пауза" in text or "воспроизведение" in text:
        answer = media_play_pause()

    elif "следующий трек" in text or "следующая песня" in text:
        answer = media_next_track()

    elif "предыдущий трек" in text or "предыдущая песня" in text:
        answer = media_prev_track()

    elif "скопируй" in text and "ответ" in text:
        answer = copy_last_answer()

    else:
        answer = ask_gpt_with_tools(user_text)

    last_answer = answer
    return answer


# ---------- Ответ пользователю ----------

def respond(answer):
    print(f"Джарвис: {answer}")
    show_text_window("Джарвис", answer)
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