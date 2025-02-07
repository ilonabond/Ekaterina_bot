from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_student
from config import ADMIN_ID
from utils import start_menu, student_keyboard, admin_keyboard

router = Router()


class AuthState(StatesGroup):
    login = State()
    password = State()

# ====== КОМАНДА /START ======
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=start_menu())


@router.message(Command("login"))
async def start_auth(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш логин:")
    await state.set_state(AuthState.login)


@router.message(AuthState.login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите ваш пароль:")
    await state.set_state(AuthState.password)


@router.message(AuthState.password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student = get_student(data["login"])

    if student and student[1] == message.text:  # Проверка пароля
        await message.answer(f"Добро пожаловать, {student[2]}!", reply_markup=student_keyboard())
    elif message.from_user.id == ADMIN_ID:
        await message.answer("Вы вошли как администратор.", reply_markup=admin_keyboard())
    else:
        await message.answer("Неверный логин или пароль.")

    await state.clear()
