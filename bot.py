import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
import sqlite3
import logging

# Установка рівня логування
logging.basicConfig(level=logging.INFO)

# Шлях до бази даних (автоматично визначає шлях відносно файлу)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'genshin_bot.db')


def connect_db():
    logging.info(f"Підключення до бази даних {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    logging.info("Підключено до бази даних.")
    return conn


conn = connect_db()
cursor = conn.cursor()

# Стани
WAITING_FOR_ACCOUNT_CHOICE = 1
WAITING_FOR_UID = 2
WAITING_FOR_UID_LOGIN = 3
WAITING_FOR_NAME = 4
WAITING_FOR_HAND_LEVEL = 5
WAITING_FOR_E_SKILL_LEVEL = 6
WAITING_FOR_BURST_LEVEL = 7
WAITING_FOR_TALENT_DAYS = 8
WAITING_FOR_CHARACTER_NAME_UPDATE = 9
WAITING_FOR_HAND_LEVEL_UPDATE = 10
WAITING_FOR_E_SKILL_LEVEL_UPDATE = 11
WAITING_FOR_BURST_LEVEL_UPDATE = 12
WAITING_FOR_TALENT_CHOICE = 13
WAITING_FOR_TALENT_UPDATE = 14
WAITING_FOR_DAY_INPUT = 15



# Функція /start
async def start(update: Update, context):
    logging.info("Команда /start отримана")
    await update.message.reply_text(
        "Привіт! Вибери одну з опцій:\n"
        "1. Створити новий акаунт\n"
        "2. Увійти в існуючий акаунт"
    )
    return WAITING_FOR_ACCOUNT_CHOICE


# Обробка вибору користувача після /start
async def account_choice(update: Update, context):
    choice = update.message.text.strip()

    if choice == "1":
        await update.message.reply_text("Введи свій UID для створення нового акаунту:")
        return WAITING_FOR_UID
    elif choice == "2":
        await update.message.reply_text("Введи свій UID, щоб увійти в акаунт:")
        return WAITING_FOR_UID_LOGIN
    else:
        await update.message.reply_text("Невірний вибір! Введи 1 для створення акаунту або 2 для входу.")
        return WAITING_FOR_ACCOUNT_CHOICE


# Збереження нового UID
async def save_uid(update: Update, context):
    uid = update.message.text.strip()

    if not uid.isdigit() or len(uid) != 9:
        await update.message.reply_text("UID має складатися з 9 цифр. Спробуй ще раз.")
        return WAITING_FOR_UID

    cursor.execute("SELECT COUNT(*) FROM users WHERE uid = ?", (uid,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (uid) VALUES (?)", (uid,))
        conn.commit()
        context.user_data["uid"] = uid
        await update.message.reply_text(f"UID {uid} збережено! Можеш додавати персонажів командою /add_character.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Цей UID вже існує в базі даних.")
        return ConversationHandler.END


# Вхід в акаунт
async def login_to_account(update: Update, context):
    uid = update.message.text.strip()

    if not uid.isdigit() or len(uid) != 9:
        await update.message.reply_text("UID має складатися з 9 цифр. Спробуй ще раз.")
        return WAITING_FOR_UID_LOGIN

    cursor.execute("SELECT COUNT(*) FROM users WHERE uid = ?", (uid,))
    if cursor.fetchone()[0] == 1:
        context.user_data["uid"] = uid
        await update.message.reply_text("Успішний вхід!\n"
                                        "Можеш додавати персонажів командою /add_character\n "
                                        "або переглянути персонажів командою /show_characters\n "
                                        "або знайти персонажів за днем /find_characters_by_day\n "
                                        "або оновити дані персонажа /update_character\n ")
        return ConversationHandler.END
    else:
        await update.message.reply_text("UID не знайдено. Спробуй ще раз або створіть новий акаунт.")
        return WAITING_FOR_UID_LOGIN


# Додавання персонажа
async def add_character(update: Update, context):
    if "uid" not in context.user_data:
        await update.message.reply_text("Будь ласка, спочатку увійди в акаунт командою /start.")
        return ConversationHandler.END

    await update.message.reply_text("Введи ім'я персонажа:")
    return WAITING_FOR_NAME


async def save_character_name(update: Update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введи рівень таланту (рука):")
    return WAITING_FOR_HAND_LEVEL


async def save_hand_level(update: Update, context):
    context.user_data["hand_level"] = int(update.message.text)
    await update.message.reply_text("Введи рівень таланту (ешка):")
    return WAITING_FOR_E_SKILL_LEVEL


async def save_e_skill_level(update: Update, context):
    context.user_data["e_skill_level"] = int(update.message.text)
    await update.message.reply_text("Введи рівень таланту (ультимейт):")
    return WAITING_FOR_BURST_LEVEL


async def save_burst_level(update: Update, context):
    context.user_data["burst_level"] = int(update.message.text)
    await update.message.reply_text("Введи дні для талантів (наприклад, середа, субота):")
    return WAITING_FOR_TALENT_DAYS


async def save_talent_days(update: Update, context):
    cursor.execute('''INSERT INTO characters (uid, name, hand_level, e_skill_level, burst_level, talent_days)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (context.user_data["uid"], context.user_data["name"],
                    context.user_data["hand_level"], context.user_data["e_skill_level"],
                    context.user_data["burst_level"], update.message.text))
    conn.commit()
    await update.message.reply_text(f"Персонаж {context.user_data['name']} додано успішно!"
                                    f"Можеш додавати персонажів командою /add_character\n "
                                    "або переглянути персонажів командою /show_characters\n "
                                    "або знайти персонажів за днем /find_characters_by_day\n "
                                    "або оновити дані персонажа /update_character\n ")
    return ConversationHandler.END


def normalize_talent_days():
    logging.info("Початок нормалізації даних talent_days...")
    cursor.execute("SELECT id, talent_days FROM characters")
    rows = cursor.fetchall()
    for row in rows:
        record_id, talent_days = row
        updated_days = ', '.join(day.strip().lower() for day in talent_days.split('/'))
        cursor.execute("UPDATE characters SET talent_days = ? WHERE id = ?", (updated_days, record_id))
    conn.commit()
    logging.info("Нормалізація даних завершена.")


async def show_characters(update: Update, context):
    uid = context.user_data.get("uid")
    if not uid:
        await update.message.reply_text("Будь ласка, спочатку увійди в акаунт командою /start.")
        return

    cursor.execute("SELECT name, hand_level, e_skill_level, burst_level, talent_days FROM characters WHERE uid = ?", (uid,))
    characters = cursor.fetchall()

    if characters:
        response = "Твої персонажі:\n"
        for idx, char in enumerate(characters, start=1):
            response += (f"{idx}. Ім'я: {char[0]}\n"
                         f"   Таланти (рука/ешка/ульт): {char[1]}/{char[2]}/{char[3]}\n"
                         f"   Дні талантів: {char[4]}\n\n")

            # Якщо довжина повідомлення перевищує 3000 символів, надсилаємо його та починаємо нове
            if len(response) > 3000:
                await update.message.reply_text(response)
                response = ""

        # Надсилаємо залишок повідомлення, якщо є
        if response:
            await update.message.reply_text(response)
    else:
        await update.message.reply_text("Немає персонажів для цього UID.")


# Пошук персонажів за днем
async def find_characters_by_day(update: Update, context):
    await update.message.reply_text("Будь ласка, введи день тижня (наприклад, понеділок, середа, субота):")


async def request_day(update: Update, context):
    await update.message.reply_text("Будь ласка, введи день тижня (наприклад, понеділок, середа, субота):")
    return WAITING_FOR_DAY_INPUT


async def show_characters_by_day(update: Update, context):
    day = update.message.text.strip().lower()

    # Перевірка на коректність введеного дня
    valid_days = ["понеділок", "вівторок", "середа", "четвер", "пятниця", "п'ятниця", "субота", "неділя"]
    if day not in valid_days:
        await update.message.reply_text("Невірний день тижня! Введи один із наступних днів: "
                                        "понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя.")
        return WAITING_FOR_DAY_INPUT

    uid = context.user_data.get("uid")
    if not uid:
        await update.message.reply_text("Будь ласка, спочатку увійди в акаунт командою /start.")
        return ConversationHandler.END

    # Запит до бази даних для пошуку персонажів за днем
    search_pattern = f"%{day.lower()}%"
    cursor.execute('''SELECT name, hand_level, e_skill_level, burst_level, talent_days
                      FROM characters
                      WHERE uid = ? AND LOWER(talent_days) LIKE ?''', (uid, search_pattern))
    characters = cursor.fetchall()  # Витягуємо результати запиту

    # Перевірка, чи є результати
    if characters:
        response = f"Ось персонажі, у яких є день {day.capitalize()}:\n"
        for idx, char in enumerate(characters, start=1):
            response += (f"{idx}. Ім'я: {char[0]}\n"
                         f"   Таланти (рука/ешка/ульт): {char[1]}/{char[2]}/{char[3]}\n"
                         f"   Дні талантів: {char[4]}\n\n")
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(f"Немає персонажів для обраного дня: {day.capitalize()}.")

    return ConversationHandler.END


# Функція для початку оновлення персонажа
async def update_character(update: Update, context):
    uid = context.user_data.get("uid")
    if not uid:
        await update.message.reply_text("Будь ласка, спочатку увійди в акаунт командою /start.")
        return ConversationHandler.END

    await update.message.reply_text("Введи ім'я персонажа, якого ти хочеш оновити:")
    return WAITING_FOR_CHARACTER_NAME_UPDATE


# Перевірка існування персонажа та показ меню талантів
async def update_character_name(update: Update, context):
    uid = context.user_data["uid"]
    name = update.message.text.strip()
    context.user_data["name"] = name

    # Перевірка наявності персонажа
    cursor.execute("SELECT hand_level, e_skill_level, burst_level FROM characters WHERE uid = ? AND name = ?", (uid, name))
    character = cursor.fetchone()

    if not character:
        await update.message.reply_text("Персонажа з таким ім'ям не знайдено. Перевірте ім'я та спробуйте знову.")
        return ConversationHandler.END

    # Збереження поточних рівнів талантів у контексті
    context.user_data["hand_level"] = character[0]
    context.user_data["e_skill_level"] = character[1]
    context.user_data["burst_level"] = character[2]

    # Виведення поточних рівнів талантів і вибір для оновлення
    await update.message.reply_text(
        f"Поточні рівні талантів персонажа {name}:\n"
        f"1. Рука: {character[0]}\n"
        f"2. Ешка: {character[1]}\n"
        f"3. Ультимейт: {character[2]}\n\n"
        "Вибери талант, який хочеш оновити (введи 1, 2 або 3):"
    )
    return WAITING_FOR_TALENT_CHOICE


# Обробка вибору таланту
async def choose_talent_to_update(update: Update, context):
    choice = update.message.text.strip()
    if choice == "1":
        context.user_data["talent_to_update"] = "hand_level"
        await update.message.reply_text("Введи новий рівень таланту (рука):")
        return WAITING_FOR_TALENT_UPDATE
    elif choice == "2":
        context.user_data["talent_to_update"] = "e_skill_level"
        await update.message.reply_text("Введи новий рівень таланту (ешка):")
        return WAITING_FOR_TALENT_UPDATE
    elif choice == "3":
        context.user_data["talent_to_update"] = "burst_level"
        await update.message.reply_text("Введи новий рівень таланту (ультимейт):")
        return WAITING_FOR_TALENT_UPDATE
    else:
        await update.message.reply_text("Невірний вибір. Введи 1, 2 або 3.")
        return WAITING_FOR_TALENT_CHOICE


# Оновлення обраного таланту
async def update_talent_level(update: Update, context):
    try:
        new_level = int(update.message.text.strip())
        if new_level < 1 or new_level > 15:
            await update.message.reply_text("Рівень таланту має бути в межах від 1 до 15. Спробуй знову.")
            return WAITING_FOR_TALENT_UPDATE
    except ValueError:
        await update.message.reply_text("Введи числове значення для рівня таланту.")
        return WAITING_FOR_TALENT_UPDATE

    # Оновлення даних у базі
    uid = context.user_data["uid"]
    name = context.user_data["name"]
    talent_column = context.user_data["talent_to_update"]

    cursor.execute(f"UPDATE characters SET {talent_column} = ? WHERE uid = ? AND name = ?", (new_level, uid, name))
    conn.commit()

    await update.message.reply_text(
        f"Рівень таланту '{talent_column}' персонажа {name} оновлено до {new_level}!\n"
        "Хочеш оновити ще один талант? Введи команду /update_character або завершуй оновлення."
    )
    return ConversationHandler.END


# Обробники команд
account_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        WAITING_FOR_ACCOUNT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, account_choice)],
        WAITING_FOR_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_uid)],
        WAITING_FOR_UID_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_to_account)],
    },
    fallbacks=[CommandHandler("start", start)]
)

character_handler = ConversationHandler(
    entry_points=[CommandHandler("add_character", add_character)],
    states={
        WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_character_name)],
        WAITING_FOR_HAND_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_hand_level)],
        WAITING_FOR_E_SKILL_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_e_skill_level)],
        WAITING_FOR_BURST_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_burst_level)],
        WAITING_FOR_TALENT_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_talent_days)],
    },
    fallbacks=[CommandHandler("start", start)]
)

update_character_handler = ConversationHandler(
    entry_points=[CommandHandler("update_character", update_character)],
    states={
        WAITING_FOR_CHARACTER_NAME_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_character_name)],
        WAITING_FOR_TALENT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_talent_to_update)],
        WAITING_FOR_TALENT_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_talent_level)],
    },
    fallbacks=[CommandHandler("start", start)]
)

find_by_day_handler = ConversationHandler(
    entry_points=[CommandHandler("find_characters_by_day", request_day)],  # Замість "show_characters_by_day"
    states={
        WAITING_FOR_DAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_characters_by_day)],
    },
    fallbacks=[CommandHandler("start", start)]
)


if __name__ == "__main__":
    normalize_talent_days()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(account_handler)
    application.add_handler(character_handler)
    application.add_handler(CommandHandler("show_characters", show_characters))
    application.add_handler(update_character_handler)
    application.add_handler(find_by_day_handler)
    application.run_polling()



