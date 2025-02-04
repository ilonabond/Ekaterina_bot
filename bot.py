import logging
import asyncio
import aiosqlite
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

ADMIN_PHONE = "+79818862605"  # Укажи свой Telegram ID

API_TOKEN = TOKEN

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
    update_type = State()

class HomeworkState(StatesGroup):
    waiting_for_homework = State()


start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Регистрация")],
        [KeyboardButton(text="🔑 Войти")],
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
        [KeyboardButton(text="📋 Список студентов")],
        [KeyboardButton(text="📋 Просмотреть домашки"), KeyboardButton(text="📈 Обновить прогресс")],
        [KeyboardButton(text="📆 Обновить расписание"), KeyboardButton(text="📚 Обновить домашку")]
    ],
    resize_keyboard=True
)


# ====== КОМАНДА /START ======
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=start_menu)

@dp.message(F.text == "🔑 Регистрация")
async def register_student(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте свой номер телефона.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True
    ))
    await state.set_state(RegisterState.waiting_for_name)  # Новый state для получения номера телефона

@dp.message(RegisterState.waiting_for_name, F.contact)
async def process_registration(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    async with aiosqlite.connect("students.db") as db:
        await db.execute(
            "INSERT INTO students (id, name, phone) VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (user_id, user_name, phone_number)
        )
        await db.commit()

    await message.answer(f"✅ {user_name}, ты зарегистрирован!\nТвой номер: `{phone_number}`", reply_markup=student_menu)
    await state.clear()

# ====== ВХОД ======
@dp.message(F.text == "🔑 Войти")
async def login_request(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте свой номер телефона для входа.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True
    ))
    await state.set_state(LoginState.waiting_for_id)  # Новый state для получения номера телефона

@dp.message(LoginState.waiting_for_id, F.contact)
async def process_login(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    if phone_number == str(ADMIN_PHONE):
        await message.answer("✅ Вход выполнен! Добро пожаловать, преподаватель!", reply_markup=admin_menu)
        await state.clear()
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT id FROM students WHERE phone=?", (phone_number,)) as cursor:
            student = await cursor.fetchone()

    await state.clear()

    if student:
        await message.answer("✅ Вход выполнен!", reply_markup=student_menu)
    else:
        await message.answer("⛔ Номер не найден! Зарегистрируйтесь сначала.")

# 🔹 Просмотр домашки
@dp.message(F.text == "📚 Моя домашка")
async def show_homework(message: types.Message):
    phone_number = message.contact.phone_number
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT homework FROM students WHERE phone_number=?", (phone_number,)) as cursor:
            result = await cursor.fetchone()

    await message.answer(f"📌 Твоя домашка:\n{result[0] if result else 'Нет домашнего задания'}")

# 🔹 Просмотр прогресса
@dp.message(F.text == "📊 Мой прогресс")
async def student_progress(message: types.Message):
    phone_number = message.contact.phone_number
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE phone_number=?", (phone_number,)) as cursor:
            result = await cursor.fetchone()

    await message.answer(f"📈 Твой прогресс:\n{result[0] if result else 'Нет данных'}")

# 🔹 Просмотр расписания
@dp.message(F.text == "📆 Моё расписание")
async def student_schedule(message: types.Message):
    phone_number = message.contact.phone_number
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT schedule FROM students WHERE phone_number=?", (phone_number,)) as cursor:
            result = await cursor.fetchone()

    await message.answer(f"📆 Твоё расписание:\n{result[0] if result else 'Нет расписания'}")


# ====== ОТПРАВКА ДОМАШКИ ======
@dp.message(F.text == "📤 Отправить ДЗ")
async def request_homework(message: types.Message, state: FSMContext):
    await message.answer("Пришлите домашнее задание (текст, фото или документ).")
    await state.set_state(HomeworkState.waiting_for_homework)

@dp.message(HomeworkState.waiting_for_homework, F.content_type.in_(['text', 'photo', 'document']))
async def receive_homework(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    text = message.text or ""

    file_id = None
    file_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    async with aiosqlite.connect("students.db") as db:
        await db.execute("INSERT INTO homeworks (student_phone, text, file_id, file_url) VALUES (?, ?, ?, ?)",
                         (phone_number, text, file_id, file_url))
        await db.commit()

    await message.answer("✅ Домашка отправлена!", reply_markup=student_menu)
    await state.clear()

@dp.message(F.text.in_(["📈 Обновить прогресс", "📆 Обновить расписание", "📚 Обновить домашку"]))
async def update_data_prompt(message: types.Message, state: FSMContext):
    if message.contact.phone_number != ADMIN_PHONE:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return

    await state.update_data(update_type=message.text)
    await state.set_state(UpdateState.waiting_for_student_phone)
    await message.answer("Введите номер телефона ученика:")

@dp.message(UpdateState.waiting_for_student_id)
async def update_student_data(message: types.Message, state: FSMContext):
    phone_number = message.text.strip()
    await state.update_data(student_phone=phone_number)
    await state.set_state(UpdateState.waiting_for_new_value)
    await message.answer("Введите новое значение:")


@dp.message(UpdateState.waiting_for_new_value)
async def update_value(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    student_phone = user_data['student_phone']
    new_value = message.text.strip()
    update_type = user_data['update_type']

    async with aiosqlite.connect("students.db") as db:
        if update_type == "📈 Обновить прогресс":
            await db.execute("UPDATE students SET progress=? WHERE phone=?", (new_value, student_phone))
        elif update_type == "📆 Обновить расписание":
            await db.execute("UPDATE students SET schedule=? WHERE phone=?", (new_value, student_phone))
        elif update_type == "📚 Обновить домашку":
            await db.execute("UPDATE students SET homework=? WHERE phone=?", (new_value, student_phone))
        await db.commit()

    await message.answer("✅ Данные обновлены!", reply_markup=admin_menu)
    await state.clear()

# 🔹 Напоминания ученикам
async def send_reminders():
    while True:
        now = datetime.now()
        async with aiosqlite.connect("students.db") as db:
            async with db.execute("SELECT phone, schedule FROM students") as cursor:
                students = await cursor.fetchall()

        for phone_number, schedule in students:
            if not schedule or schedule == "Нет расписания":
                continue
            try:
                lesson_time = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
                # Напоминание за 2 часа до урока о том, что урок скоро и надо сделать домашку
                if lesson_time - timedelta(hours=2) <= now < lesson_time - timedelta(hours=1, minutes=55):
                    await bot.send_message(phone_number, "📌 Напоминание: через 2 часа у тебя урок. Не забудь выполнить домашку.")
                # Напоминание за 5-10 минут после урока о необходимости оплаты
                elif lesson_time + timedelta(minutes=5) <= now < lesson_time + timedelta(minutes=10):
                    await bot.send_message(phone_number, "💳 Напоминание: не забудь оплатить урок.")
            except ValueError:
                continue

        await asyncio.sleep(300)  # Пауза между проверками (5 м

# ====== О РЕПЕТИТОРЕ ======
@dp.message(F.text == "ℹ️ О репетиторе")
async def about_tutor(message: types.Message):
    tutor_info = (
        "👩‍🏫 Привет! Меня зовут Екатерина, я репетитор по математике и русскому языку. "
        "Моя цель – помочь тебе разобраться в сложных темах и добиться успеха в учебе! 📚\n\n"
        "📝 Если у тебя есть вопросы по домашнему заданию, расписанию или прогрессу – не стесняйся обращаться!"
    )
    await message.answer(tutor_info)

@dp.message(F.text == "📋 Список студентов")
async def list_students(message: types.Message):
    if message.from_user.phone_number != ADMIN_PHONE:
        await message.answer("⛔ У вас нет прав для просмотра списка студентов.")
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT phone, name FROM students") as cursor:
            students = await cursor.fetchall()

    if not students:
        await message.answer("📂 В базе пока нет зарегистрированных студентов.")

    student_list = "\n".join([f"👤 {name} (Телефон: {phone})" for phone, name in students])
    await message.answer(f"📋 Список студентов:\n\n{student_list}")

# 🔹 Запуск бота
async def main():
    async with aiosqlite.connect("students.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS students (
            phone TEXT PRIMARY KEY, 
            name TEXT, 
            progress TEXT DEFAULT 'Нет данных', 
            schedule TEXT DEFAULT 'Нет расписания', 
            homework TEXT DEFAULT 'Нет домашнего задания'
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            student_phone TEXT, 
            text TEXT, 
            file_id TEXT,
            FOREIGN KEY (student_phone) REFERENCES students (phone)
        )""")
        await db.commit()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
