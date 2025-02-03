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


# Клавиатура главного меню
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Моя домашка"), KeyboardButton(text="📆 Моё расписание")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="ℹ️ О репетиторе")]
    ],
    resize_keyboard=True
)


# ====== РЕГИСТРАЦИЯ УЧЕНИКА ======
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


# ====== ПРОСМОТР РАСПИСАНИЯ ======
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


# ====== ПРОСМОТР ДОМАШКИ ======
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


# ====== ПРОСМОТР ПРОГРЕССА ======
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


# ====== ДОБАВЛЕНИЕ ПРОГРЕССА (ТОЛЬКО ДЛЯ АДМИНА) ======
@dp.message(Command("update_progress"))
async def update_progress(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и его новый прогресс через `|` (пример: `123456|Сдал тест на 90%`).")


@dp.message(lambda message: "|" in message.text and message.from_user.id == ADMIN_ID)
async def save_progress(message: types.Message):
    try:
        student_id, progress = message.text.split("|", 1)
        student_id = int(student_id.strip())
        progress = progress.strip()

        async with aiosqlite.connect("students.db") as db:
            # Проверка на существование ученика
            async with db.execute("SELECT id FROM students WHERE id=?", (student_id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    await message.answer(f"❌ Ученик с ID {student_id} не найден в базе данных.")
                    return

            await db.execute(
                "UPDATE students SET progress=? WHERE id=?", (progress, student_id)
            )
            await db.commit()

        await message.answer(f"✅ Прогресс ученика {student_id} обновлён: {progress}")
    except ValueError:
        await message.answer("❌ Неверный формат. Введите ID ученика и прогресс через `|`.")


# ====== ДОБАВЛЕНИЕ ДОМАШКИ (ТОЛЬКО ДЛЯ АДМИНА) ======
@dp.message(Command("update_homework"))
async def update_homework(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и домашнее задание через `|` (пример: `123456|Сделать тест №3`).")


@dp.message(lambda message: "|" in message.text and message.from_user.id == ADMIN_ID)
async def save_homework(message: types.Message):
    try:
        student_id, homework = message.text.split("|", 1)
        student_id = int(student_id.strip())
        homework = homework.strip()

        async with aiosqlite.connect("students.db") as db:
            # Проверка на существование ученика
            async with db.execute("SELECT id FROM students WHERE id=?", (student_id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    await message.answer(f"❌ Ученик с ID {student_id} не найден в базе данных.")
                    return

            await db.execute(
                "UPDATE students SET homework=? WHERE id=?", (homework, student_id)
            )
            await db.commit()

        await message.answer(f"✅ Домашка ученика {student_id} обновлена: {homework}")
    except ValueError:
        await message.answer("❌ Неверный формат. Введите ID ученика и задание через `|`.")


# ====== ДОБАВЛЕНИЕ РАСПИСАНИЯ (ТОЛЬКО ДЛЯ АДМИНА) ======
@dp.message(Command("update_schedule"))
async def update_schedule(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await message.answer("Введите ID ученика и расписание через `|` (пример: `123456|Занятие в среду 18:00`).")


@dp.message(lambda message: "|" in message.text and message.from_user.id == ADMIN_ID)
async def save_schedule(message: types.Message):
    try:
        student_id, schedule = message.text.split("|", 1)
        student_id = int(student_id.strip())
        schedule = schedule.strip()

        async with aiosqlite.connect("students.db") as db:
            # Проверка на существование ученика
            async with db.execute("SELECT id FROM students WHERE id=?", (student_id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    await message.answer(f"❌ Ученик с ID {student_id} не найден в базе данных.")
                    return

            await db.execute(
                "UPDATE students SET schedule=? WHERE id=?", (schedule, student_id)
            )
            await db.commit()

        await message.answer(f"✅ Расписание ученика {student_id} обновлено: {schedule}")
    except ValueError:
        await message.answer("❌ Неверный формат. Введите ID ученика и расписание через `|`.")


# Запуск бота
async def main():
    await init_db()  # Инициализация БД
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
