import logging
import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

ADMIN_ID = 123456789  # Укажите свой ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Определение состояний
class UpdateState(StatesGroup):
    waiting_for_student_id = State()
    waiting_for_new_value = State()

class HomeworkState(StatesGroup):
    waiting_for_homework = State()

# Просмотр домашки
@dp.message(F.text == "📚 Моя домашка")
async def show_homework(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT homework FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result and result[0] != "Нет домашнего задания":
                await message.answer(f"📌 Твоя домашка:\n{result[0]}")
            else:
                await message.answer("У тебя нет загруженной домашки. Попроси преподавателя добавить её!")

# Просмотр прогресса
@dp.message(F.text == "📊 Мой прогресс")
async def student_progress(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result and result[0] != "Нет данных":
                await message.answer(f"📈 Твой прогресс:\n{result[0]}")
            else:
                await message.answer("Прогресс пока не обновлён. Обратись к преподавателю!")

# Просмотр расписания
@dp.message(F.text == "📆 Моё расписание")
async def student_schedule(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT schedule FROM students WHERE id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result and result[0] != "Нет расписания":
                await message.answer(f"📆 Твоё расписание:\n{result[0]}")
            else:
                await message.answer("У тебя нет расписания. Свяжись с преподавателем!")

# Отправка домашки
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

    # Напоминание преподавателю
    await bot.send_message(ADMIN_ID, f"📌 Ученик {student_id} отправил домашку.")

    await message.answer("✅ Домашка отправлена!")
    await state.clear()

# Обновление данных учеников (прогресс, расписание, домашка)
@dp.message(F.text.in_(["📈 Обновить прогресс", "📆 Обновить расписание", "📚 Обновить домашку"]))
async def update_data_prompt(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для использования этой команды.")
        return

    await state.update_data(update_type=message.text)
    await state.set_state(UpdateState.waiting_for_student_id)
    await message.answer("Введите ID ученика, для которого хотите обновить данные:")

@dp.message(UpdateState.waiting_for_student_id)
async def update_student_data(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ ID должен быть числом! Попробуйте снова.")
        return

    await state.update_data(student_id=int(message.text))
    await state.set_state(UpdateState.waiting_for_new_value)
    await message.answer("Введите новое значение:")

@dp.message(UpdateState.waiting_for_new_value)
async def save_updated_data(message: types.Message, state: FSMContext):
    new_value = message.text.strip()
    data = await state.get_data()
    student_id = data["student_id"]
    update_type = data["update_type"]

    async with aiosqlite.connect("students.db") as db:
        if update_type == "📈 Обновить прогресс":
            await db.execute("UPDATE students SET progress = ? WHERE id = ?", (new_value, student_id))
        elif update_type == "📆 Обновить расписание":
            await db.execute("UPDATE students SET schedule = ? WHERE id = ?", (new_value, student_id))
        elif update_type == "📚 Обновить домашку":
            await db.execute("UPDATE students SET homework = ? WHERE id = ?", (new_value, student_id))
        await db.commit()

    await state.clear()
    await message.answer("✅ Данные успешно обновлены!")

# Напоминания ученикам
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
                    await bot.send_message(student_id,
                                           "📌 Напоминание: через 2 часа у тебя урок. Не забудь выполнить домашку!")

                elif lesson_time + timedelta(minutes=5) <= now < lesson_time + timedelta(minutes=10):
                    await bot.send_message(student_id, "💳 Напоминание: не забудь оплатить урок.")

            except ValueError:
                continue

        await asyncio.sleep(300)

# Запуск бота
async def main():
    async with aiosqlite.connect("students.db") as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            progress TEXT DEFAULT 'Нет данных',
            schedule TEXT DEFAULT 'Нет расписания',
            homework TEXT DEFAULT 'Нет домашнего задания'
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            text TEXT,
            file_id TEXT
        )
        ''')
        await db.commit()

    asyncio.create_task(send_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
