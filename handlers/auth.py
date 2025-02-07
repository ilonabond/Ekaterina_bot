from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_student
from config import ADMIN_ID
from utils import start_menu, student_keyboard, admin_keyboard
import aiosqlite

router = Router()

class AuthState(StatesGroup):
    login = State()
    password = State()

# ====== КОМАНДА /START ======
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=start_menu())

# ====== Кнопка "Войти" ======
@router.message(lambda message: message.text == "🔑 Войти")
async def login_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш логин (число, например: `12345`):")
    await state.set_state(AuthState.login)

# ====== Ввод логина ======
@router.message(AuthState.login)
async def process_login(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Логин должен быть числом. Попробуйте снова.")
        return

    await state.update_data(login=message.text)
    await message.answer("Введите ваш пароль (число, например: `67890`):")
    await state.set_state(AuthState.password)

# ====== Ввод пароля ======
@router.message(AuthState.password)
async def process_password(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Пароль должен быть числом. Попробуйте снова.")
        return

    data = await state.get_data()
    login, password = data["login"], message.text

    # Проверка на администратора
    if login == ADMIN_ID:
        await message.answer("✅ Вход выполнен! Добро пожаловать, преподаватель!", reply_markup=admin_keyboard())
        await state.clear()
        return

    # Проверка студента в базе данных
    async with aiosqlite.connect("students.db") as db:
        async with db.execute("SELECT name FROM students WHERE login=? AND password=?", (login, password)) as cursor:
            student = await cursor.fetchone()

    await state.clear()

    if student:
        await message.answer(f"✅ Вход выполнен, {student[0]}!", reply_markup=student_keyboard())
    else:
        await message.answer("⛔ Неверный логин или пароль!")

# ====== Команда /about_tutor или кнопка "ℹ️ О репетиторе" ======
TUTOR_INFO = """
Я ваш репетитор, и я готова помочь Вам с вашим учебным процессом!

Мои предметы:
- Математика
- Физика
- Английский язык

Свяжитесь со мной, если у вас есть вопросы.
"""

@router.message(lambda message: message.text == "ℹ️ О репетиторе" or message.text == "/about_tutor")
async def about_tutor(message: types.Message):
    await message.answer(TUTOR_INFO)
