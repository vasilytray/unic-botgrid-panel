# Dockerfile (в корне)
FROM python:3.13-slim

# # Установка системных зависимостей
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# Установка системных утилит для диагностики
RUN apt-get update && apt-get install -y \
    iputils-ping \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app

# Создаем пользователя ПЕРЕД копированием файлов
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем non-root пользователя для безопасности
# RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
