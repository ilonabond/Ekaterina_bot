from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def student_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📚 Моя домашка")],
        [KeyboardButton(text="📆 Моё расписание")],
        [KeyboardButton(text="📊 Мой прогресс")],
        [KeyboardButton(text="📤 Отправить ДЗ")]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Добавить ученика")],
        [KeyboardButton(text="❌ Удалить ученика")],
        [KeyboardButton(text="📋 Список учеников")],
        [KeyboardButton(text="📚 Обновить домашку")]
    ], resize_keyboard=True)
