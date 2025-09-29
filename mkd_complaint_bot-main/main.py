from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from telegram import BotCommand
from datetime import datetime
from dotenv import load_dotenv
import os
import openpyxl
import asyncio

# Загружаем переменные окружения из .env
load_dotenv()

# Состояния
PROBLEM_TYPE, USER_DETAILS, OTHER_PROBLEM = range(3)

# Конфигурация
TOKEN = os.getenv("TOKEN")
EXCEL_FILE = "complaints.xlsx"

# Инициализация Excel
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Дата", "ФИО", "Этаж", "Квартира", "Дом", "Домофон", "Проблема"])
    wb.save(EXCEL_FILE)

PROBLEM_TRANSLATIONS = {
    "water_leak": "Протечка воды",
    "elevator_broken": "Поломка лифта",
    "electricity_issue": "Проблемы с электричеством",
    "noisy_neighbors": "Шумные соседи",
    "garbage_not_removed": "Мусор не вывозится",
    "property_damage": "Повреждение имущества"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Проблема в доме", callback_data="house_problem")],
        [InlineKeyboardButton("Поддержка", callback_data="support")],
        [InlineKeyboardButton("Очистить чат", callback_data="clear_chat")],
        [InlineKeyboardButton("GitHub", url="https://github.com")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=markup)
    else:
        await update.callback_query.edit_message_text("Добро пожаловать! Выберите действие:", reply_markup=markup)
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 Список команд:\n"
        "/start – Главное меню\n"
        "/help – Помощь и команды\n"
        "/clear – Очистить чат (символически)\n\n"
        "Вы также можете пользоваться кнопками внутри бота."
    )
    await update.message.reply_text(text)


async def house_problem_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Протечка воды", callback_data="water_leak")],
        [InlineKeyboardButton("Поломка лифта", callback_data="elevator_broken")],
        [InlineKeyboardButton("Проблемы с электричеством", callback_data="electricity_issue")],
        [InlineKeyboardButton("Шумные соседи", callback_data="noisy_neighbors")],
        [InlineKeyboardButton("Мусор не вывозится", callback_data="garbage_not_removed")],
        [InlineKeyboardButton("Повреждение имущества", callback_data="property_damage")],
        [InlineKeyboardButton("Другая проблема", callback_data="other_problem")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Выберите проблему:", reply_markup=markup)
    return PROBLEM_TYPE

async def select_problem_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_start":
        return await start(update, context)
    if query.data == "other_problem":
        await query.edit_message_text("Опишите проблему (текстом):")
        return OTHER_PROBLEM

    context.user_data['problem_type'] = PROBLEM_TRANSLATIONS.get(query.data, query.data)
    await query.edit_message_text("Введите ФИО:")
    return USER_DETAILS

async def get_other_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['problem_type'] = update.message.text
    await update.message.reply_text("Введите ФИО:")
    return USER_DETAILS

async def ask_floor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"floor_{i}") for i in range(1, 6)],
        [InlineKeyboardButton("Ввести вручную", callback_data="manual_floor")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите этаж или введите вручную:", reply_markup=markup)

async def get_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'fio' not in context.user_data:
        context.user_data['fio'] = update.message.text
        await update.message.reply_text("Введите этаж:")
        return USER_DETAILS
    elif 'floor' not in context.user_data:
        if not update.message.text.isdigit():  # Проверка, что этаж — это число
            await update.message.reply_text("❌ Введите правильный этаж (только числа):")
            return USER_DETAILS
        context.user_data['floor'] = update.message.text
        await update.message.reply_text("Введите номер квартиры:")
        return USER_DETAILS
    elif 'apartment' not in context.user_data:
        context.user_data['apartment'] = update.message.text
        await update.message.reply_text("Введите номер дома:")
        return USER_DETAILS
    elif 'house_number' not in context.user_data:
        context.user_data['house_number'] = update.message.text
        await update.message.reply_text("Введите номер домофона:")
        return USER_DETAILS
    else:
        context.user_data['intercom'] = update.message.text

        try:
            wb = openpyxl.load_workbook(EXCEL_FILE)
            ws = wb.active
            ws.append([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                context.user_data['fio'],
                context.user_data['floor'],
                context.user_data['apartment'],
                context.user_data['house_number'],
                context.user_data['intercom'],
                context.user_data['problem_type']
            ])
            wb.save(EXCEL_FILE)
            print("✅ Данные успешно сохранены в таблицу Excel.")
        except Exception as e:
            print(f"Ошибка при записи в файл Excel: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении данных. Попробуйте еще раз.")

        await update.message.reply_text("✅ Жалоба отправлена!")

        # Очищаем данные пользователя перед началом новой сессии
        context.user_data.clear()

        # Возвращаем пользователя в начало или завершение процесса
        return ConversationHandler.END

async def support_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📞 +7 (123) 456-78-90\n📧 support@example.com\n🕒 9:00-18:00 (Пн-Пт)",
                                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_start")]]))

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("История очищена (символически).",
                                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_start")]]))

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Очистка истории недоступна через API Telegram. Используйте кнопку в меню.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "house_problem":
        return await house_problem_menu(update, context)
    elif data == "support":
        return await support_info(update, context)
    elif data == "clear_chat":
        return await clear_chat(update, context)
    elif data == "back_to_start":
        return await start(update, context)

async def floor_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("floor_"):
        floor = query.data.split("_")[1]
        context.user_data["floor"] = floor
        context.user_data["step"] = "apartment"
        await query.edit_message_text(f"Вы выбрали этаж: {floor}")
        await query.message.reply_text("Введите номер квартиры:")
        return USER_DETAILS

    elif query.data == "manual_floor":
        context.user_data["step"] = "floor"
        await query.edit_message_text("Введите этаж вручную:")
        return USER_DETAILS

async def set_bot_commands(app: Application):
    commands = [
        BotCommand("start", "Главное меню"),
        BotCommand("help", "Помощь и команды"),
        BotCommand("clear", "Очистка чата (символическая)")
    ]
    await app.bot.set_my_commands(commands)

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_click)],
    states={
        PROBLEM_TYPE: [CallbackQueryHandler(select_problem_type)],
        OTHER_PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_other_problem)],
        USER_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_details),
            CallbackQueryHandler(floor_keyboard_handler, pattern="^floor_\\d+$|^manual_floor$")
        ]
    },
    fallbacks=[CommandHandler("start", start)]
)

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_click))

    app.post_init = set_bot_commands
    app.run_polling()

if __name__ == "__main__":
    main()
