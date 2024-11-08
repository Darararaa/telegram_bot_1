# Використовуємо Python 3.10 як базовий образ
FROM python:3.10

# Копіюємо файли бота в контейнер
WORKDIR /app
COPY . /app

# Встановлюємо залежності
RUN pip install -r requirements.txt

# Запускаємо бота
CMD ["python", "bot.py"]
