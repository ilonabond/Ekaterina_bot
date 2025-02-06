import sqlite3
import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()


async def send_reminders():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT login, schedule FROM students")
    students = cursor.fetchall()
    conn.close()

    now = datetime.now()

    for login, schedule in students:
        if not schedule:
            continue
        lesson_time = datetime.strptime(schedule, "%d.%m.%y %H:%M")

        # За 2 часа до урока
        if now + timedelta(hours=2) >= lesson_time:
            await bot.send_message(login, "Напоминание: Через 2 часа у вас урок!")

        # Через 5 минут после урока
        if now >= lesson_time + timedelta(minutes=5):
            await bot.send_message(login, "Напоминание: Не забудьте оплатить урок.")

        # Очистка прошедших уроков через 15 минут
        if now >= lesson_time + timedelta(minutes=15):
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET schedule = '' WHERE login = ?", (login,))
            conn.commit()
            conn.close()


def setup_scheduler():
    scheduler.add_job(send_reminders, "interval", minutes=5)
    scheduler.start()


async def main():
    setup_scheduler()  # Запускаем напоминания без аргументов
    while True:
        await asyncio.sleep(3600)  # Запуск в бесконечном цикле


if __name__ == "__main__":
    asyncio.run(main())  # Запуск асинхронного цикла
