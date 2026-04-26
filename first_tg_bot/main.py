import asyncio
from os import getenv
from dotenv import load_dotenv # type: ignore
import requests

from aiogram import Bot, Dispatcher # type: ignore
from aiogram.filters import CommandStart, Command # type: ignore
from aiogram.types import Message # type: ignore
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

if (requests.get("https://api.telegram.org").status_code == 200):
    print("Соединение с api.telegram.org прошло успешно")
else:
    print("Ошибка. Нет соединения с api.telegram.org")

dp = Dispatcher()
load_dotenv()

user_messages = {} 

async def send_and_track(message: Message, text: str, **kwargs):    # туть остановился :)
    user_id = message.from_user.id
    user_messages.setdefault(user_id, [])  
    
    user_messages[user_id].append(message.message_id)

    msg = await message.answer(text)

    user_messages[user_id].append(msg.message_id)

    return msg

@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добро пожаловать в стартовое меню", callback_data="click")],
        [InlineKeyboardButton(text="Очистить", callback_data="clear")]
    ])

    await message.answer("Выберите опцию:", reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    await callback.answer()

    if callback.data == "click":
        await callback.message.answer("Фишки работают!!!")

    elif callback.data == "clear":
        user_id = callback.from_user.id
        ids = user_messages.get(user_id, [])

        if ids:
            await callback.bot.delete_messages(
                chat_id = callback.message.chat.id,
                message_ids = ids
            )

        user_messages[user_id] = []

@dp.message(Command("clear"))
async def clear_handler(message: Message):
    user_id = message.from_user.id

    user_messages.setdefault(user_id, []).append(message.message_id) 

    ids = user_messages.get(user_id, [])

    print("IDs:", ids) # для проверки получения id-шников

    if not ids:
        await message.answer("Нечего удалять(")
        return
    
    await message.bot.delete_messages(
        chat_id = message.chat.id,
        message_ids = ids
    )

    user_messages[user_id] = [] # Очистка списка

@dp.message()
async def echo_handler(message: Message) -> None:
    await send_and_track(message, f"Ты написал: {message.text}")

async def main() -> None:
    TOKEN = getenv("BOT_TOKEN")
    if TOKEN is None:
        raise ValueError("BOT_TOKEN is not set")
    bot = Bot(token=TOKEN) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())