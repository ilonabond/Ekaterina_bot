# bot.py
import logging
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import auth, student, admin
from scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем экземпляр бота
bot = Bot(token=BOT_TOKEN)

# Создаем экземпляр диспетчера
dp = Dispatcher(bot)

async def main():
    # Подключаем роутеры для различных частей бота
    dp.include_router(auth.router)
    dp.include_router(student.router)
    dp.include_router(admin.router)

    # Запускаем планировщик для напоминаний
    setup_scheduler()  # Запуск напоминаний

    # Запускаем бота
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())  # Запуск асинхронного цикла
