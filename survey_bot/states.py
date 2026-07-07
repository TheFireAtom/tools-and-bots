from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    """
    Состояния (шаги) опроса.

    Каждое состояние — это "какой вопрос сейчас ждёт бот от пользователя".
    aiogram сам запоминает, в каком состоянии находится КАЖДЫЙ пользователь
    отдельно — тебе не нужно вручную хранить это в переменных.
    """

    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_city = State()