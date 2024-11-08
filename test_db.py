import sqlite3

# Шлях до бази даних
DB_PATH = 'data/genshin_bot.db'


# Перевірка підключення
def test_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY)")
        uid = input("Введіть UID для перевірки: ")
        cursor.execute("INSERT OR IGNORE INTO users (uid) VALUES (?)", (uid,))
        conn.commit()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print("Користувачі в базі даних:", users)
        conn.close()
    except Exception as e:
        print("Помилка підключення до бази даних:", e)


if __name__ == "__main__":
    test_db()
