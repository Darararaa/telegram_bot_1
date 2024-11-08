# Вибираємо базовий образ Python
FROM python:3.9-slim

# Встановлюємо залежності
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо увесь код в контейнер
COPY . /app

# Вказуємо команду для запуску вашого бота
CMD ["python", "your_bot_file.py"]
