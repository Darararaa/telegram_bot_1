# Вибираємо базовий образ Python
FROM python:3.10-slim

# Встановлюємо залежності
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо увесь код в контейнер
COPY . .

ENV TZ=Europe/Kyiv
# Вказуємо команду для запуску вашого бота
CMD ["python", "bot.py"]
