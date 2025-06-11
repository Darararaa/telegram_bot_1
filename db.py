import sqlite3
import os

# Шлях до бази даних (автоматично визначає шлях відносно файлу)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'genshin_bot.db')

# Перевірка на існування каталогу, якщо його немає — створюємо
if not os.path.exists('data'):
    os.makedirs('data')


def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      uid TEXT PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS characters (
                      id INTEGER PRIMARY KEY,
                      uid TEXT,
                      name TEXT,
                      hand_level INTEGER,
                      e_skill_level INTEGER,
                      burst_level INTEGER,
                      talent_days TEXT,
                      FOREIGN KEY(uid) REFERENCES users(uid))''')
    conn.commit()
    conn.close()
