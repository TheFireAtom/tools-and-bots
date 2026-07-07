from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from states import SurveyStates
from texts import (
    START_TEXT,
    NAME_INVALID_TEXT,
    ASK_AGE_TEXT,
    AGE_NOT_A_NUMBER_TEXT,
    AGE_OUT_OF_RANGE_TEXT,
    ASK_CITY_TEXT,
    CITY_INVALID_TEXT,
    RESULT_TEXT,
    CANCEL_TEXT,
    CANCEL_NOTHING_TO_CANCEL_TEXT,
)

router = Router()


def is_valid_name_or_city(text: str) -> bool:
    """
    Проверяет, что текст похож на имя/город: только буквы,
    пробелы и дефисы (для двойных имён вроде "Санкт-Петербург").

    Не пускаем цифры и спецсимволы, но разрешаем кириллицу и латиницу.
    """
    stripped = text.strip()

    if not stripped:
        return False

    return all(char.isalpha() or char in " -" for char in stripped)


# ---------- Старт опроса ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Начинаем опрос: переводим пользователя в состояние
    "ждём имя" и задаём первый вопрос.
    """
    await state.set_state(SurveyStates.waiting_for_name)
    await message.answer(START_TEXT)


# ---------- Отмена опроса (работает на любом шаге) ----------

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    /cancel должен работать независимо от того, на каком вопросе
    сейчас находится пользователь — поэтому у этого хендлера
    нет привязки к конкретному состоянию.
    """
    current_state = await state.get_state()

    if current_state is None:
        # Пользователь не в опросе — отменять нечего
        await message.answer(CANCEL_NOTHING_TO_CANCEL_TEXT)
        return

    # Полностью сбрасываем состояние и все сохранённые ответы
    await state.clear()
    await message.answer(CANCEL_TEXT)


# ---------- Шаг 1: получаем имя, спрашиваем возраст ----------

@router.message(SurveyStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """
    Этот хендлер сработает ТОЛЬКО если пользователь сейчас находится
    в состоянии waiting_for_name — aiogram сам проверяет это перед вызовом.
    """
    name = message.text or ""

    if not is_valid_name_or_city(name):
        await message.answer(NAME_INVALID_TEXT)
        return  # остаёмся в том же состоянии, ждём повторный ввод

    # Сохраняем ответ в данные состояния — они привязаны к конкретному
    # пользователю и доступны на следующих шагах опроса.
    await state.update_data(name=name.strip())

    # Переходим к следующему вопросу
    await state.set_state(SurveyStates.waiting_for_age)
    await message.answer(ASK_AGE_TEXT.format(name=name.strip()))


# ---------- Шаг 2: получаем возраст (с валидацией), спрашиваем город ----------

@router.message(SurveyStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    age_text = message.text or ""

    # Проверяем, что пользователь ввёл именно число
    if not age_text.isdigit():
        await message.answer(AGE_NOT_A_NUMBER_TEXT)
        return  # остаёмся в том же состоянии, ждём повторный ввод

    age = int(age_text)

    # Проверяем разумные границы возраста
    if age < 1 or age > 120:
        await message.answer(AGE_OUT_OF_RANGE_TEXT)
        return  # остаёмся в том же состоянии

    await state.update_data(age=age)
    await state.set_state(SurveyStates.waiting_for_city)
    await message.answer(ASK_CITY_TEXT)


# ---------- Шаг 3: получаем город, показываем итог ----------

@router.message(SurveyStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text or ""

    if not is_valid_name_or_city(city):
        await message.answer(CITY_INVALID_TEXT)
        return  # остаёмся в том же состоянии, ждём повторный ввод

    # get_data() достаёт ВСЕ ответы, сохранённые на предыдущих шагах
    data = await state.get_data()

    # Опрос завершён — очищаем состояние, чтобы бот "забыл" этот диалог
    await state.clear()

    await message.answer(
        RESULT_TEXT.format(
            name=data.get("name"),
            age=data.get("age"),
            city=city.strip(),
        )
    )