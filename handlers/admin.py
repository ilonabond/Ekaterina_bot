from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_student, remove_student, update_student, get_all_students, get_homework_submissions
from config import ADMIN_ID

router = Router()

class AddStudentState(StatesGroup):
    login = State()
    password = State()
    name = State()

@router.message(Command("add_student"))
async def add_student_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    await message.answer("Введите логин ученика:")
    await state.set_state(AddStudentState.login)

@router.message(AddStudentState.login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите пароль ученика:")
    await state.set_state(AddStudentState.password)

@router.message(AddStudentState.password)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer("Введите имя ученика:")
    await state.set_state(AddStudentState.name)

@router.message(AddStudentState.name)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    add_student(data["login"], data["password"], message.text)
    await message.answer("Ученик добавлен!")
    await state.clear()

@router.message(Command("remove_student"))
async def remove_student_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    await message.answer("Введите логин ученика, которого хотите удалить:")

@router.message()
async def process_remove_student(message: types.Message):
    remove_student(message.text)
    await message.answer("Ученик удален.")

@router.message(Command("students"))
async def list_students(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    students = get_all_students()
    response = "\n".join([f"{s[1]} (логин: {s[0]})" for s in students])
    await message.answer(f"Список учеников:\n{response}")

@router.message(Command("homework_submissions"))
async def list_homework_submissions(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    submissions = get_homework_submissions()
    response = "\n".join([f"{s[0]}: {s[1]}" for s in submissions])
    await message.answer(f"Отправленные домашние задания:\n{response}")

@router.message(Command("update_schedule"))
async def update_schedule_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    await message.answer("Введите логин ученика и новое расписание (логин | расписание):")

@router.message()
async def process_update_schedule(message: types.Message):
    try:
        login, schedule = message.text.split(" | ")
        update_student(login, "schedule", schedule)
        await message.answer("Расписание обновлено!")
    except:
        await message.answer("Ошибка формата, попробуйте снова.")

@router.message(Command("update_progress"))
async def update_progress_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    await message.answer("Введите логин ученика и новый прогресс (логин | прогресс):")

@router.message()
async def process_update_progress(message: types.Message):
    try:
        login, progress = message.text.split(" | ")
        update_student(login, "progress", progress)
        await message.answer("Прогресс обновлен!")
    except:
        await message.answer("Ошибка формата, попробуйте снова.")

@router.message(Command("update_homework"))
async def update_homework_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Доступ запрещен!")
    await message.answer("Введите логин ученика и новое ДЗ (логин | домашка):")

@router.message()
async def process_update_homework(message: types.Message):
    try:
        login, homework = message.text.split(" | ")
        update_student(login, "homework", homework)
        await message.answer("Домашнее задание обновлено!")
    except:
        await message.answer("Ошибка формата, попробуйте снова.")
