import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # MemoryStorage хранит состояния пользователей прямо в оперативной памяти
    # процесса Python. Это самый простой вариант для обучения и тестов.
    #
    # Важно: если бот перезапустится (или упадёт), ВСЕ состояния и данные
    # опроса пользователей потеряются — они начнут диалог заново.
    # Для реального продакшена вместо MemoryStorage используют
    # RedisStorage — тогда состояния переживают перезапуск бота.
    storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")