import logging
import asyncio
import aiosqlite
import pytz
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os

MOSCOW_TZ = pytz.timezone("Europe/Moscow")  # Устанавливаем

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

ADMIN_ID = int(os.getenv("ADMIN_ID", "1000461829"))  # Укажи свой Telegram ID

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔹 Состояния
class LoginState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class AddStudentState(StatesGroup):
    waiting_for_name = State()
    waiting_for_login = State()
    waiting_for_password = State()

class DeleteStudentState(StatesGroup):
    waiting_for_login = State()

class UpdateState(StatesGroup):
    waiting_for_student_login = State()
    waiting_for_new_value = State()
    update_type = State()

# Клавиатуры
start_menu = ReplyKeyboardMarkup(
    keyboard=[
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
        [KeyboardButton(text="➕ Добавить ученика"), KeyboardButton(text="❌ Удалить ученика")],
        [KeyboardButton(text="📋 Список учеников"), KeyboardButton(text="📋 Просмотреть домашки")],
        [KeyboardButton(text="📈 Обновить прогресс"), KeyboardButton(text="📆 Обновить расписание")],
        [KeyboardButton(text="📚 Обновить домашку")]
    ],
    resize_keyboard=True
)

# ====== КОМАНДА /START ======
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=start_menu)

# ====== ВХОД ======
@dp.message(F.text == "🔑 Войти")
async def login_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш логин (число, например: `12345`):")
    await state.set_state(LoginState.waiting_for_login)

@dp.message(LoginState.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Логин должен быть числом. Попробуйте снова.")
        return

    await state.update_data(login=message.text)
    await message.answer("Введите ваш пароль (число, например: `67890`):")
    await state.set_state(LoginState.waiting_for_password)

@dp.message(LoginState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Пароль должен быть числом. Попробуйте снова.")
        return

    data = await state.get_data()
    login, password = data["login"], message.text

    if message.from_user.id == ADMIN_ID:
        await message.answer("✅ Вход выполнен! Добро пожаловать, преподаватель!", reply_markup=admin_menu)
        await state.clear()
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT name FROM students WHERE login=? AND password=?", (login, password)) as cursor:
            student = await cursor.fetchone()

    await state.clear()

    if student:
        await message.answer(f"✅ Вход выполнен, {student[0]}!", reply_markup=student_menu)
    else:
        await message.answer("⛔ Неверный логин или пароль!")

# ====== ДОБАВЛЕНИЕ УЧЕНИКА ======
@dp.message(F.text == "➕ Добавить ученика")
async def add_student_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для добавления учеников.")
        return

    await message.answer("Введите имя ученика:")
    await state.set_state(AddStudentState.waiting_for_name)

@dp.message(AddStudentState.waiting_for_name)
async def add_student_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите логин (число):")
    await state.set_state(AddStudentState.waiting_for_login)

@dp.message(AddStudentState.waiting_for_login)
async def add_student_login(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Логин должен быть числом. Попробуйте снова.")
        return

    await state.update_data(login=message.text)
    await message.answer("Введите пароль (число):")
    await state.set_state(AddStudentState.waiting_for_password)

@dp.message(AddStudentState.waiting_for_password)
async def add_student_password(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Пароль должен быть числом. Попробуйте снова.")
        return

    data = await state.get_data()
    name, login, password = data["name"], data["login"], message.text

    async with aiosqlite.connect("students.db") as db:
        await db.execute("INSERT INTO students (login, password, name) VALUES (?, ?, ?)", (login, password, name))
        await db.commit()

    await message.answer(f"✅ Ученик {name} добавлен!\n🔑 Логин: {login}\n🔐 Пароль: {password}")
    await state.clear()

# ====== УДАЛЕНИЕ УЧЕНИКА ======
@dp.message(F.text == "❌ Удалить ученика")
async def delete_student_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для удаления учеников.")
        return

    await message.answer("Введите логин ученика для удаления:")
    await state.set_state(DeleteStudentState.waiting_for_login)

@dp.message(DeleteStudentState.waiting_for_login)
async def delete_student(message: types.Message, state: FSMContext):
    login = message.text

    async with aiosqlite.connect("students.db") as db:
        await db.execute("DELETE FROM students WHERE login=?", (login,))
        await db.commit()

    await message.answer(f"✅ Ученик с логином {login} удалён.")
    await state.clear()

# 🔹 Просмотр списка учеников
@dp.message(F.text == "📋 Список учеников")
async def list_students(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для просмотра списка учеников.")
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT login, name FROM students") as cursor:
            students = await cursor.fetchall()

    if not students:
        await message.answer("📂 В базе пока нет учеников.")
    else:
        student_list = "\n".join([f"👤 {name} (Логин: {login})" for login, name in students])
        await message.answer(f"📋 Список учеников:\n\n{student_list}")


# ====== ФУНКЦИИ ДЛЯ УЧЕНИКОВ ======
@dp.message(lambda message: message.text == "📚 Моя домашка")
async def show_homework(message: types.Message, state: FSMContext):
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT homework FROM students WHERE login=?", (str(message.from_user.id),)) as cursor:
            result = await cursor.fetchone()

    homework_text = result[0] if result else "Нет домашнего задания"
    await message.answer(f"📌 Твоя домашка:\n{homework_text}")


@dp.message(lambda message: message.text == "📆 Моё расписание")
async def student_schedule(message: types.Message):
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT schedule FROM students WHERE login=?", (str(message.from_user.id),)) as cursor:
            result = await cursor.fetchone()

    schedule_text = result[0] if result else "Нет расписания"
    await message.answer(f"📆 Твоё расписание:\n{schedule_text}")


@dp.message(lambda message: message.text == "📊 Мой прогресс")
async def view_progress(message: types.Message):
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT progress FROM students WHERE login=?", (str(message.from_user.id),)) as cursor:
            result = await cursor.fetchone()

    progress_text = result[0] if result else "Нет данных о прогрессе"
    await message.answer(f"📈 Твой прогресс:\n{progress_text}")



@dp.message(lambda message: message.text == "📤 Отправить ДЗ")
async def request_homework(message: types.Message, state: FSMContext):
    await message.answer("Пришлите домашнее задание (текст или фото).")
    await state.set_state(UpdateState.waiting_for_new_value)


@dp.message(UpdateState.waiting_for_new_value, F.content_type.in_([types.ContentType.TEXT, types.ContentType.PHOTO]))
async def receive_homework(message: types.Message, state: FSMContext):
    async with aiosqlite.connect("students.db") as db:
        if message.text:
            await db.execute("UPDATE students SET homework=? WHERE login=?", (message.text, str(message.from_user.id)))
        elif message.photo:
            photo_id = message.photo[-1].file_id
            await db.execute("UPDATE students SET homework=? WHERE login=?", (photo_id, str(message.from_user.id)))

        await db.commit()

    await message.answer("✅ Домашнее задание отправлено!")
    await state.clear()



# ====== ФУНКЦИИ ДЛЯ ПРЕПОДАВАТЕЛЯ ======
@dp.message(lambda message: message.text == "📋 Просмотреть домашки")
async def view_homeworks(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT phone, homework FROM students") as cursor:
            homeworks = await cursor.fetchall()

    homework_list = "\n\n".join([f"📱 {phone}: {hw}" for phone, hw in homeworks])
    await message.answer(f"📚 Домашние задания:\n\n{homework_list}")


@dp.message(F.text.in_(["📈 Обновить прогресс", "📆 Обновить расписание", "📚 Обновить домашку"]))
async def update_student_info(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    update_type = "progress" if "прогресс" in message.text else "schedule" if "расписание" in message.text else "homework"
    await state.update_data(update_type=update_type)

    await message.answer("Введите логин ученика:")
    await state.set_state(UpdateState.waiting_for_student_login)

@dp.message(UpdateState.waiting_for_student_login)
async def get_student_login(message: types.Message, state: FSMContext):
    await state.update_data(student_login=message.text.strip())

    update_type = (await state.get_data()).get("update_type")
    if update_type == "schedule":
        await message.answer("Введите расписание в формате `ДД.ММ.ГГГГ ЧЧ:ММ`:")
    elif update_type == "progress":
        await message.answer("Введите новый прогресс ученика:")
    elif update_type == "homework":
        await message.answer("Введите новое домашнее задание:")

    await state.set_state(UpdateState.waiting_for_new_value)

@dp.message(UpdateState.waiting_for_new_value)
async def save_new_value(message: types.Message, state: FSMContext):
    new_value = message.text.strip()
    data = await state.get_data()
    student_login = data.get("student_login")
    update_type = data.get("update_type")

    if update_type == "schedule":
        try:
            datetime.strptime(new_value, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer("❌ Неверный формат даты! Введите в формате `ДД.ММ.ГГГГ ЧЧ:ММ`.")
            return

    async with aiosqlite.connect("students.db") as db:
        await db.execute(f"UPDATE students SET {update_type}=? WHERE login=?", (new_value, student_login))
        await db.commit()

    await message.answer("✅ Данные обновлены.")
    await state.clear()



# ====== НАПОМИНАНИЯ ======
async def send_reminders():
    while True:
        now = datetime.now(pytz.utc).astimezone(MOSCOW_TZ)  # Получаем текущее московское время
        async with aiosqlite.connect("students.db") as db:
            async with db.execute("SELECT login, schedule FROM students") as cursor:
                students = await cursor.fetchall()

        for login, schedule in students:
            if not schedule:
                continue
            try:
                # Преобразуем время урока в московское время
                lesson_time = datetime.strptime(schedule, "%d.%m.%Y %H:%M").replace(tzinfo=MOSCOW_TZ)

                # 🔹 Напоминание за 2 часа до урока
                if lesson_time - timedelta(hours=2) <= now < lesson_time - timedelta(hours=1, minutes=55):
                    await bot.send_message(login, "📌 Напоминание: через 2 часа у тебя урок, не забудь сделать ДЗ.")

                # 🔹 Напоминание за 5 минут после урока
                elif lesson_time + timedelta(minutes=5) <= now < lesson_time + timedelta(minutes=10):
                    await bot.send_message(login, "💳 Напоминание: не забудь оплатить урок.")

                # 🔹 Удаление прошедшего урока из базы (через 15 минут после урока)
                elif now >= lesson_time + timedelta(minutes=15):
                    async with aiosqlite.connect("students.db") as db:
                        await db.execute("UPDATE students SET schedule=NULL WHERE login=?", (login,))
                        await db.commit()
                        await bot.send_message(login, "✅ Урок завершен, расписание обновлено.")

            except ValueError:
                continue

        await asyncio.sleep(300)  # Проверка каждые 5 минут


# ====== О РЕПЕТИТОРЕ ======
@dp.message(lambda message: message.text == "ℹ️ О репетиторе")
async def about_tutor(message: types.Message):
    tutor_info = ("👩‍🏫 Здравствуйте, я - репетитор Екатерина, преподаю математику и русский язык."
                  "Помогу разобраться в сложных темах! 📚")
    await message.answer(tutor_info)


# 🔹 Запуск и настройка базы данных
async def setup_database():
    async with aiosqlite.connect("students.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS students (
            login TEXT PRIMARY KEY,
            password TEXT,
            name TEXT,
            schedule TEXT DEFAULT NULL,
            progress TEXT DEFAULT NULL,
            homework TEXT DEFAULT NULL
        )""")
        await db.commit()


async def main():
    await setup_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
