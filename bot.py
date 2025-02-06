import logging
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import auth, student, admin
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Регистрируем обработчики роутеров
    dp.include_router(auth.router)
    dp.include_router(student.router)
    dp.include_router(admin.router)

    # Запускаем напоминания
    setup_scheduler()  # Теперь не передаем bot в setup_scheduler, т.к. bot доступен глобально
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())  # Запускаем асинхронный цикл
