import logging
import asyncio
import aiosqlite
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

ADMIN_ID = 123456789  # Укажи свой Telegram ID

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔹 Состояния
class LoginState(StatesGroup):
    waiting_for_id = State()

class RegisterState(StatesGroup):
    waiting_for_name = State()

class UpdateState(StatesGroup):
    waiting_for_student_id = State()
    waiting_for_new_value = State()

class HomeworkState(StatesGroup):
    waiting_for_homework = State()

start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Регистрация"), KeyboardButton(text="🔑 Войти")],
        [KeyboardButton(text="ℹ️ О репетиторе")]
    ],
    resize_keyboard=True
)

student_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Моя домашка"), KeyboardButton(text="📆 Моё расписание")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="📤 Отправить ДЗ")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Просмотреть домашки"), KeyboardButton(text="📈 Обновить прогресс")],
        [KeyboardButton(text="📆 Обновить расписание"), KeyboardButton(text="📚 Обновить домашку")]
    ],
    resize_keyboard=True
)


# ====== КОМАНДА /START ======
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=start_menu)

# ====== РЕГИСТРАЦИЯ ======
@dp.message(F.text == "🔑 Регистрация")
async def register_student(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    student_id = random.randint(10000, 99999)  # Генерируем персональный ID

    async with aiosqlite.connect("students.db") as db:
        await db.execute(
            "INSERT INTO students (id, name, student_id) VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (user_id, user_name, student_id)
        )
        await db.commit()

    await message.answer(f"✅ {user_name}, ты зарегистрирован!\nТвой ID: `{student_id}`\nИспользуй его для входа.", reply_markup=student_menu)

# ====== ВХОД ======
@dp.message(F.text == "🔑 Войти")
async def login_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш ID:")
    await state.set_state(LoginState.waiting_for_id)

@dp.message(LoginState.waiting_for_id)
async def process_login(message: types.Message, state: FSMContext):
    student_id = message.text.strip()

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id FROM students WHERE student_id=?", (student_id,)) as cursor:
            student = await cursor.fetchone()

    await state.clear()

    if student:
        await message.answer("✅ Вход выполнен!", reply_markup=student_menu)
    else:
        await message.answer("⛔ ID не найден!")


# 🔹 Просмотр домашки
@dp.message(F.text == "📚 Моя домашка")
async def show_homework(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT homework FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result and result[0] != "Нет домашнего задания":
        await message.answer(f"📌 Твоя домашка:\n{result[0]}")
    else:
        await message.answer("У тебя нет загруженной домашки.")

# 🔹 Просмотр прогресса
@dp.message(F.text == "📊 Мой прогресс")
async def student_progress(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result and result[0] != "Нет данных":
        await message.answer(f"📈 Твой прогресс:\n{result[0]}")
    else:
        await message.answer("Прогресс пока не обновлён.")

# 🔹 Просмотр расписания
@dp.message(F.text == "📆 Моё расписание")
async def student_schedule(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT schedule FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result and result[0] != "Нет расписания":
        await message.answer(f"📆 Твоё расписание:\n{result[0]}")
    else:
        await message.answer("У тебя нет расписания.")

# 🔹 Отправка домашки учеником
@dp.message(F.text == "📤 Отправить домашку")
async def request_homework(message: types.Message, state: FSMContext):
    await message.answer("Пришлите домашнее задание (текст, фото или документ).")
    await state.set_state(HomeworkState.waiting_for_homework)

@dp.message(HomeworkState.waiting_for_homework, F.content_type.in_(['text', 'photo', 'document']))
async def receive_homework(message: types.Message, state: FSMContext):
    student_id = message.from_user.id
    text = message.text or ""

    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    async with aiosqlite.connect("students.db") as db:
        await db.execute("INSERT INTO homeworks (student_id, text, file_id) VALUES (?, ?, ?)",
                         (student_id, text, file_id))
        await db.commit()

    await bot.send_message(ADMIN_ID, f"📌 Ученик {student_id} отправил домашку.")
    await message.answer("✅ Домашка отправлена!")
    await state.clear()

# 🔹 Напоминания ученикам
async def send_reminders():
    while True:
        now = datetime.now()
        async with aiosqlite.connect("students.db") as db:
            async with db.execute("SELECT id, schedule FROM students") as cursor:
                students = await cursor.fetchall()

        for student_id, schedule in students:
            if not schedule or schedule == "Нет расписания":
                continue
            try:
                lesson_time = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
                if lesson_time - timedelta(hours=2) <= now < lesson_time - timedelta(hours=1, minutes=55):
                    await bot.send_message(student_id, "📌 Напоминание: через 2 часа у тебя урок.")
                elif lesson_time + timedelta(minutes=5) <= now < lesson_time + timedelta(minutes=10):
                    await bot.send_message(student_id, "💳 Напоминание: не забудь оплатить урок.")
            except ValueError:
                continue

        await asyncio.sleep(300)

# 🔹 Запуск бота
async def main():
    async with aiosqlite.connect("students.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY, name TEXT, progress TEXT DEFAULT 'Нет данных', 
            schedule TEXT DEFAULT 'Нет расписания', homework TEXT DEFAULT 'Нет домашнего задания'
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, text TEXT, file_id TEXT
        )""")
        await db.commit()

    asyncio.create_task(send_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
