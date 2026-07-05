from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from keyboards import main_menu_keyboard, back_to_menu_keyboard

# Router — это способ группировать хендлеры отдельно от main.py.
# Удобно, когда бот вырастет и хендлеров станет много.
router = Router()


# ---------- Тексты (в реальном проекте это можно вынести в отдельный texts.py) ----------

WELCOME_TEXT = (
    "👋 Привет! Я бот-визитка компании <b>Example Studio</b>.\n\n"
    "Здесь ты можешь узнать про наши услуги, цены и связаться с нами.\n"
    "Выбери, что тебя интересует 👇"
)

SERVICES_TEXT = (
    "📋 <b>Наши услуги:</b>\n\n"
    "• Разработка Telegram-ботов\n"
    "• Автоматизация бизнес-процессов\n"
    "• Интеграция с внешними сервисами (оплата, CRM, API)\n"
    "• Поддержка и доработка существующих ботов"
)

PRICE_TEXT = (
    "💰 <b>Прайс (ориентировочно):</b>\n\n"
    "• Простой бот-визитка — от 3 000 ₽\n"
    "• Бот с анкетой/квизом — от 5 000 ₽\n"
    "• Бот-магазин с оплатой — от 15 000 ₽\n"
    "• Индивидуальный проект — расчёт по ТЗ\n\n"
    "Точная цена зависит от сложности задачи."
)

CONTACTS_TEXT = (
    "📞 <b>Контакты:</b>\n\n"
    "Telegram: @your_username\n"
    "Email: example@example.com\n\n"
    "Напиши нам — обсудим твою задачу!"
)

PORTFOLIO_TEXT = (
    "⭐ <b>Портфолио:</b>\n\n"
    "1. Бот-каталог для интернет-магазина\n"
    "2. Бот для записи на консультации\n"
    "3. Бот-опросник с сохранением результатов\n\n"
    "(Здесь можно добавить ссылки на реальные проекты, когда они появятся)"
)


# ---------- Хендлеры ----------

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Срабатывает на команду /start"""
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery):
    await callback.message.edit_text(SERVICES_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()  # убирает "часики" на кнопке


@router.callback_query(F.data == "price")
async def show_price(callback: CallbackQuery):
    await callback.message.edit_text(PRICE_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    await callback.message.edit_text(CONTACTS_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    await callback.message.edit_text(PORTFOLIO_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()