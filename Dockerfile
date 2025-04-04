# Використовуємо офіційний Python образ
FROM python:3.10-slim

# Встановлюємо залежності для psycopg2
RUN apt-get update && apt-get install -y libpq-dev

# Встановлюємо pip та необхідні бібліотеки
RUN pip install --upgrade pip
RUN pip install psycopg2-binary

# Створюємо директорію для твоєї програми
WORKDIR /app

# Копіюємо файли з твоєї локальної системи в контейнер
COPY . /app

# Встановлюємо залежності з requirements.txt, якщо вони є
RUN pip install -r requirements.txt

# Вказуємо команду для запуску твого додатку
CMD ["python", "mtrepo.py"]
