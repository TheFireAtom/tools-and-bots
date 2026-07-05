from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from keyboards import main_menu_keyboard, back_to_menu_keyboard
from texts import (
    WELCOME_TEXT,
    SERVICES_TEXT,
    PRICE_TEXT,
    CONTACTS_TEXT,
    PORTFOLIO_TEXT,
)

# Router — это способ группировать хендлеры отдельно от main.py.
# Удобно, когда бот вырастет и хендлеров станет много.
router = Router()

async def safe_edit(callback: CallbackQuery, text: str, keyboard) -> None:
    """
    Безопасно редактирует сообщение под кнопкой.

    callback.message в aiogram имеет тип Message | InaccessibleMessage.
    InaccessibleMessage — редкий случай (например, сообщение слишком старое
    или было удалено), и у него НЕТ метода edit_text. Поэтому сначала
    проверяем, что перед нами настоящий Message, и только потом редактируем.
    """
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)

# ---------- Хендлеры ----------

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Срабатывает на команду /start"""
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery):
    await safe_edit(callback, SERVICES_TEXT, back_to_menu_keyboard())
    await callback.answer()  # убирает "часики" на кнопке


@router.callback_query(F.data == "price")
async def show_price(callback: CallbackQuery):
    await safe_edit(callback, PRICE_TEXT, back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    await safe_edit(callback, CONTACTS_TEXT, back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    await safe_edit(callback, PORTFOLIO_TEXT, back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await safe_edit(callback, WELCOME_TEXT, main_menu_keyboard())
    await callback.answer()