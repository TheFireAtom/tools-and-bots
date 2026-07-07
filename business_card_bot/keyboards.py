from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота-визитки."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📋 Услуги", callback_data="services")
    builder.button(text="💰 Прайс", callback_data="price")
    builder.button(text="📞 Контакты", callback_data="contacts")
    builder.button(text="⭐ Портфолио", callback_data="portfolio")

    # Располагаем кнопки по 2 в ряд
    builder.adjust(2, 2)

    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка 'Назад' для возврата в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")
    return builder.as_markup()