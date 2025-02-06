from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import get_student, submit_homework

router = Router()

@router.message(Command("homework"))
async def show_homework(message: types.Message):
    student = get_student(message.from_user.id)
    if student:
        await message.answer(f"Ваше домашнее задание: {student[5]}")
    else:
        await message.answer("Вы не зарегистрированы.")

@router.message(Command("schedule"))
async def show_schedule(message: types.Message):
    student = get_student(message.from_user.id)
    if student:
        await message.answer(f"Ваше расписание: {student[3]}")
    else:
        await message.answer("Вы не зарегистрированы.")

@router.message(Command("progress"))
async def show_progress(message: types.Message):
    student = get_student(message.from_user.id)
    if student:
        await message.answer(f"Ваш прогресс: {student[4]}")
    else:
        await message.answer("Вы не зарегистрированы.")

@router.message(Command("submit_homework"))
async def request_homework(message: types.Message):
    await message.answer("Отправьте текст или фото домашнего задания.")

@router.message()
async def receive_homework(message: types.Message):
    if message.photo:
        submission = message.photo[-1].file_id
    else:
        submission = message.text

    submit_homework(message.from_user.id, submission)
    await message.answer("Ваше домашнее задание отправлено репетитору!")
