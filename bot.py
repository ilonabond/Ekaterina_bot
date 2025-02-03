import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import os

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# ID преподавателя (замени на свой)
ADMIN_ID = 123456789  # Замените на ваш реальный ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к базе данных (асинхронное)
async def init_db():
    async with aiosqlite.connect("students.db") as db:
        # Создание таблицы, если её нет
        await db.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            progress TEXT DEFAULT 'Нет данных',
            homework TEXT DEFAULT 'Нет домашнего задания',
            schedule TEXT DEFAULT 'Нет расписания'
        )
        ''')
        await db.commit()

# Функция для добавления колонок, если их нет
async def add_columns():
    async with aiosqlite.connect("students.db") as db:
        try:
            # Добавление столбца 'homework', если его нет
            await db.execute("ALTER TABLE students ADD COLUMN homework TEXT DEFAULT 'Нет домашнего задания'")
            await db.execute("ALTER TABLE students ADD COLUMN schedule TEXT DEFAULT 'Нет расписания'")
            await db.commit()
        except Exception as e:
            # Если столбцы уже существуют, это может вызвать исключение
            print(f"Ошибка при добавлении колонок: {e}")

# Клавиатура главного меню
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Моя домашка"), KeyboardButton(text="📆 Моё расписание")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="ℹ️ О репетиторе")]
    ],
    resize_keyboard=True
)

# Регистрируем пользователя
@dp.message(Command("register"))
async def register_student(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    async with aiosqlite.connect("students.db") as db:
        await db.execute(
            "INSERT INTO students (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
            (user_id, user_name)
        )
        await db.commit()

    await message.answer(f"✅ {user_name}, ты зарегистрирован! Теперь ты можешь пользоваться ботом.", reply_markup=menu)

# Просмотр расписания
@dp.message(lambda message: message.text.strip().lower() == "📆 моё расписание")
async def show_schedule(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT schedule FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer(f"📅 Твоё расписание:\n{result[0]}")
            else:
                await message.answer("Ты не зарегистрирован! Введи /register")

# Просмотр домашки
@dp.message(lambda message: message.text.strip().lower() == "📚 моя домашка")
async def show_homework(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT homework FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer(f"📌 Твоя домашка:\n{result[0]}")
            else:
                await message.answer("Ты не зарегистрирован! Введи /register")

# Просмотр прогресса
@dp.message(lambda message: message.text.strip().lower() == "📊 мой прогресс")
async def student_progress(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer(f"📈 Твой прогресс:\n{result[0]}")
            else:
                await message.answer("Ты не зарегистрирован! Введи /register")

# Запуск бота
async def main():
    await init_db()  # Инициализация БД
    await add_columns()  # Добавление колонок (если их нет)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
