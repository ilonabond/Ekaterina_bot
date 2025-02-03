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
            progress TEXT
        )
        ''')
        await db.commit()


# Клавиатура главного меню (исправлено)
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Домашние задания"), KeyboardButton(text="📆 Расписание")],
        [KeyboardButton(text="📊 Прогресс"), KeyboardButton(text="ℹ️ О репетиторе")]
    ],
    resize_keyboard=True
)
# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    user_name = message.from_user.first_name if message.from_user else "ученик"
    await message.answer(f"Привет, {user_name}! 👋\nЯ – бот репетитора Екатерины. Чем могу помочь?", reply_markup=menu)


# Команда /help
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer("Я могу отправлять тебе расписание, домашние задания и следить за твоим прогрессом.")


# Раздел «О репетиторе»
@dp.message(lambda message: message.text.strip().lower() == "ℹ️ о репетиторе")
async def about_teacher(message: types.Message):
    await message.answer("Привет! Я Екатерина – репетитор по математике и русскому языку. Готовлю к ОГЭ и ЕГЭ. 📚")


# Раздел «Прогресс ученика»
@dp.message(lambda message: message.text.strip().lower() == "📊 прогресс")
async def student_progress(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                await message.answer(f"📈 Твой прогресс: {result[0]}")
            else:
                await message.answer("Данных пока нет. Заполню после первых занятий!")


# Запуск бота в aiogram v3
async def main():
    await init_db()  # Инициализация БД
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
