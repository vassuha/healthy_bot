from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
import asyncio
import csv
from pathlib import Path

# Настройка GigaChat
llm = GigaChat(
    credentials="ODlmNjNiMzQtYmRjYS00MmE5LWI4YTgtNTNjMjQ2ZGYyMWI5OmUwOTFhYzUyLWViNzktNGQzYy04ZjZiLTAwODJlOWFlYjMwMA==",  # Замените на ваш ключ GigaChat
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False,
    streaming=False,
)

# Путь к CSV-файлу
CSV_FILE = Path("user_data.csv")

# Токен Telegram-бота
BOT_TOKEN = "7573247715:AAENXOKfSdvr3QMhKpP4oVSDt18iycjob6M"

# Словари для хранения данных
user_data = {}  # Хранит регистрационные данные пользователей
user_context = {}  # Хранит контексты для GigaChat

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для FSM
class Registration(StatesGroup):
    name = State()
    age = State()
    height = State()
    weight = State()
    gender = State()
    activity = State()
    goal = State()

# Функция для записи данных в CSV
def write_to_csv(data: dict):
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["user_id", "name", "age", "height", "weight", "gender", "activity", "goal"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# Стартовая клавиатура
def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать регистрацию", callback_data="start_registration")],
            [InlineKeyboardButton(text="Общение с персональным помощником", callback_data="gigachat")],
        ]
    )

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я твой персональный помощник по поддержанию здорового образа жизни. Выбери действие:",
        reply_markup=start_keyboard(),
    )

# Обработчик нажатия на кнопки
@dp.callback_query()
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    if callback.data == "start_registration":
        await callback.message.answer("Как тебя зовут?")
        await state.set_state(Registration.name)

    elif callback.data == "gigachat":
        user_id = callback.from_user.id

        # Проверка регистрации
        if user_id not in user_data:
            await callback.message.answer("Сначала пройдите регистрацию!")
            return

        # Создаем персонализированный контекст для GigaChat
        user_info = user_data[user_id]
        user_context[user_id] = [
            SystemMessage(content=(
                f"Ты профессиональный бот для поддержки здорового образа жизни. Пользователь {user_info['name']} {user_info['age']} лет, рост {user_info['height']} см, вес {user_info['weight']} кг, пол: {user_info['gender']}. "
                f"Его уровень активности: {user_info['activity']}. Его цель: {user_info['goal']}. Опираясь на эти данные, помоги ему решить его вопросы. Чаще обращайся к нему по имени и упоминай в диалоге информацию, которую ты о нем знаешь."
            ))
        ]

        await callback.message.answer(
            "Вы можете начать общение с персональным помощником. Напишите свой вопрос:"
        )

# FSM: обработчик имени
@dp.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Registration.age)

# FSM: обработчик возраста
@dp.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Какой у тебя рост (в сантиметрах)?")
    await state.set_state(Registration.height)

# FSM: обработчик роста
@dp.message(Registration.height)
async def process_height(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите рост числом.")
        return
    await state.update_data(height=int(message.text))
    await message.answer("Какой у тебя вес (в килограммах)?")
    await state.set_state(Registration.weight)

# FSM: обработчик веса
@dp.message(Registration.weight)
async def process_weight(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите вес числом.")
        return
    await state.update_data(weight=int(message.text))
    await message.answer("Какой у тебя пол? (мужской/женский)")
    await state.set_state(Registration.gender)

# FSM: обработчик пола
@dp.message(Registration.gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text.lower() not in ["мужской", "женский"]:
        await message.answer("Пожалуйста, укажите пол: мужской или женский.")
        return
    await state.update_data(gender=message.text.lower())
    await message.answer("Какой у тебя уровень активности? (низкий/средний/высокий)")
    await state.set_state(Registration.activity)

# FSM: обработчик уровня активности
@dp.message(Registration.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.answer("Какая у тебя цель? (например: похудеть, набрать вес, поддерживать форму)")
    await state.set_state(Registration.goal)

# FSM: обработчик цели
@dp.message(Registration.goal)
async def process_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    data["goal"] = message.text
    data["user_id"] = user_id

    # Сохраняем данные в словарь и CSV
    user_data[user_id] = data
    write_to_csv(data)

    await message.answer(
        "Регистрация завершена!\n\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Рост: {data['height']} см\n"
        f"Вес: {data['weight']} кг\n"
        f"Пол: {data['gender']}\n"
        f"Активность: {data['activity']}\n"
        f"Цель: {data['goal']}",
        reply_markup=start_keyboard(),
    )
    await state.clear()

# Обработчик сообщений для общения с GigaChat
@dp.message()
async def handle_gigachat(message: Message):
    user_id = message.from_user.id

    if user_id not in user_context:
        await message.answer("Вы еще не начали общение с персональным помощником. Нажмите кнопку в меню.")
        return

    user_context[user_id].append(HumanMessage(content=message.text))

    try:
        response = llm.invoke(user_context[user_id])
        user_context[user_id].append(response)
        await message.answer(response.content)
    except Exception as e:
        await message.answer("Произошла ошибка при общении с персональным помощником.")
        print(f"Ошибка: {e}")

# Основной блок запуска
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
