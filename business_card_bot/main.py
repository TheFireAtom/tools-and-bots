import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import router

async def main():
    # Настройка логов — полезно для отладки, увидишь ошибки в консоли
    logging.basicConfig(level=logging.INFO)

    # Создаём бота. parse_mode=HTML позволяет использовать <b>, <i> и т.д. в текстах
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    ) 

    # Диспетчер — раздаёт входящие сообщения нужным хендлерам
    dp = Dispatcher()
    dp.include_router(router)

    # Удаляем возможные старые апдейты, чтобы бот не отвечал на старые сообщения при рестарте
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем polling — бот постоянно спрашивает Telegram: "есть новые сообщения?"
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")