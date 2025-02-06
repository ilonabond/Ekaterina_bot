import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            login TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            schedule TEXT,
            progress TEXT,
            homework TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS homework_submissions (
            login TEXT NOT NULL,
            submission TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_student(login, password, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students VALUES (?, ?, ?, '', '', '')", (login, password, name))
    conn.commit()
    conn.close()

def remove_student(login):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE login = ?", (login,))
    conn.commit()
    conn.close()

def get_student(login):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE login = ?", (login,))
    student = cursor.fetchone()
    conn.close()
    return student

def update_student(login, field, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE students SET {field} = ? WHERE login = ?", (value, login))
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT login, name FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

def submit_homework(login, submission):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO homework_submissions VALUES (?, ?)", (login, submission))
    conn.commit()
    conn.close()

def get_homework_submissions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM homework_submissions")
    submissions = cursor.fetchall()
    conn.close()
    return submissions
