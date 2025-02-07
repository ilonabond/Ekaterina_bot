import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import auth, student, admin
from scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем экземпляр бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Создаем диспетчер
dp = Dispatcher()

async def main():
    dp["bot"] = bot  # Регистрируем бота в контексте
    dp.include_router(auth.router)
    dp.include_router(student.router)
    dp.include_router(admin.router)

    setup_scheduler(bot)  # Передаем бота в планировщик

    await dp.start_polling(bot)  # Передаем бота в start_polling()

if __name__ == "__main__":
    asyncio.run(main())
