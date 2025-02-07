import sqlite3
import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()


async def send_reminders(bot: Bot):
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

        try:
            if now + timedelta(hours=2) >= lesson_time:
                await bot.send_message(login, "Напоминание: Через 2 часа у вас урок!")

            if now >= lesson_time + timedelta(minutes=5):
                await bot.send_message(login, "Напоминание: Не забудьте оплатить урок.")

            if now >= lesson_time + timedelta(minutes=15):
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE students SET schedule = '' WHERE login = ?", (login,))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Ошибка при отправке сообщения {login}: {e}")


def setup_scheduler(bot: Bot):
    scheduler.add_job(send_reminders, "interval", minutes=5, args=[bot])
    scheduler.start()
