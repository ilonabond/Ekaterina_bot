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

start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Регистрация"), KeyboardButton(text="🔑 Войти")]
    ],
    resize_keyboard=True
)

# Клавиатура главного меню
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Моя домашка"), KeyboardButton(text="📆 Моё расписание")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="ℹ️ О репетиторе")],
        [KeyboardButton(text="❓ Задать вопрос преподавателю")]
    ],
    resize_keyboard=True
)

# ====== КОМАНДА /START ======
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Проверка, зарегистрирован ли пользователь
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer(f"Привет, {user_name}! Ты уже зарегистрирован.", reply_markup=main_menu)
            else:
                await message.answer(f"Привет, {user_name}! Для начала зарегистрируйся.", reply_markup=start_menu)


# ====== РЕГИСТРАЦИЯ УЧЕНИКА ======
@dp.message(lambda message: message.text.strip().lower() == "🔑 регистрация")
async def register_student(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    async with aiosqlite.connect("students.db") as db:
        await db.execute(
            "INSERT INTO students (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
            (user_id, user_name)
        )
        await db.commit()

    await message.answer(f"✅ {user_name}, ты зарегистрирован! Теперь ты можешь пользоваться ботом.", reply_markup=main_menu)


# ====== ВХОД ПО ID ======
@dp.message(lambda message: message.text.strip().lower() == "🔑 войти")
async def login_by_id(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer("Ты успешно вошёл!", reply_markup=main_menu)
            else:
                await message.answer("Ты не зарегистрирован! Введи /register для регистрации.")


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

@dp.message(Command("update_schedule"))
async def update_schedule(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и расписание через `|` (пример: `123456|Занятие в среду 18:00`).")


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

@dp.message(Command("update_homework"))
async def update_homework(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и домашнее задание через `|` (пример: `123456|Сделать тест №3`).")


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

@dp.message(Command("update_progress"))
async def update_progress(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и его новый прогресс через `|` (пример: `123456|Сдал тест на 90%`).")

# ====== О репетиторе ======
@dp.message(lambda message: message.text.strip().lower() == "ℹ️ о репетиторе")
async def about_tutor(message: types.Message):
    # Информация о репетиторе
    tutor_info = (
        "👨‍🏫 Здравствуйте, меня зовут Екатерина. Я репетитор по математике и русскому языку. Моя цель - помочь Вам улучшить свои навыки.\n"
        "Если у тебя есть вопросы или нужно уточнение по домашке, прогрессу или расписанию - всегда обращайся!"
    )

    await message.answer(tutor_info)

# ====== ЗАДАТЬ ВОПРОС ПРЕПОДАВАТЕЛЮ ======
@dp.message(lambda message: message.text.strip().lower() == "❓ задать вопрос преподавателю")
async def ask_question(message: types.Message):
    # Запросить у ученика текст вопроса
    await message.answer("Напиши свой вопрос, и преподаватель ответит тебе в ближайшее время.")

# ====== ОБРАБОТКА ВОПРОСА УЧЕНИКА ======
@dp.message(lambda message: message.text.strip() != "❓ задать вопрос преподавателю")
async def save_and_notify_teacher(message: types.Message):
    student_id = message.from_user.id
    question = message.text.strip()

    async with aiosqlite.connect("students.db") as db:
        # Сохраняем вопрос в базе данных
        await db.execute(
            "INSERT INTO questions (student_id, question) VALUES (?, ?)",
            (student_id, question)
        )
        await db.commit()

    # Отправка уведомления преподавателю
    teacher_message = f"Ученик с ID {student_id} задал вопрос:\n{question}"

    await bot.send_message(ADMIN_ID, teacher_message)
    await message.answer("Ваш вопрос был отправлен преподавателю. Он ответит вам в ближайшее время.")

# Подключение к базе данных и создание таблицы для вопросов
async def init_db():
    async with aiosqlite.connect("students.db") as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            progress TEXT DEFAULT 'Нет данных',
            homework TEXT DEFAULT 'Нет домашнего задания',
            schedule TEXT DEFAULT 'Нет расписания'
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            question TEXT,
            answered BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
        ''')

        await db.commit()

# ====== ПРЕПОДАВАТЕЛЬ ПРОСМАТРИВАЕТ ВОПРОСЫ ======
@dp.message(lambda message: message.text.strip().lower() == "📋 Просмотр вопросов")
async def view_questions(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id, student_id, question FROM questions WHERE answered = FALSE") as cursor:
            questions = await cursor.fetchall()

    if not questions:
        await message.answer("Нет новых вопросов от учеников.")
        return

    for q in questions:
        student_id, question = q[1], q[2]
        await message.answer(f"Вопрос от ученика с ID {student_id}:\n{question}\n\nНапишите свой ответ.")

# ====== ПРЕПОДАВАТЕЛЬ ОТВЕЧАЕТ НА ВОПРОС ======
@dp.message(lambda message: message.text.strip() != "📋 Просмотр вопросов" and message.from_user.id == ADMIN_ID)
async def answer_question(message: types.Message):
    # Ответ преподавателя на вопрос
    answer = message.text.strip()

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id, student_id, question FROM questions WHERE answered = FALSE LIMIT 1") as cursor:
            question = await cursor.fetchone()

        if question:
            question_id, student_id, student_question = question
            # Сохраняем ответ и помечаем вопрос как ответственный
            await db.execute("UPDATE questions SET answered = TRUE WHERE id = ?", (question_id,))
            await db.commit()

            # Отправляем ответ ученику
            await bot.send_message(student_id, f"Ответ на ваш вопрос:\n{answer}")
            await message.answer(f"Ответ на вопрос от ученика с ID {student_id} был отправлен.")
        else:
            await message.answer("Нет вопросов, на которые можно ответить.")

# Запуск бота
async def main():
    await init_db()  # Инициализация БД
    await add_columns()  # Добавление колонок (если их нет)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
