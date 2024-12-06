# Messaging Service

Messaging Service — это веб-приложение для отправки сообщений и уведомлений через различные каналы, такие как Telegram. Проект использует **FastAPI**, **PostgreSQL**, **Redis** и **Celery**, а также контейнеризацию через **Docker**.

---

## Основные технологии

- **FastAPI**: для создания API.
- **PostgreSQL**: для хранения данных.
- **Redis**: как брокер задач для Celery.
- **Celery**: для выполнения фоновых задач.
- **Docker** и **Docker Compose**: для контейнеризации и управления сервисами.
- **Uvicorn**: сервер ASGI.
- **Alembic**: для миграций базы данных.

---

## Переменные окружения `.env`

Создайте файл `.env` в корне проекта и добавьте следующие переменные:

```env
# Настройки PostgreSQL
POSTGRES_USER=         # Имя пользователя для базы данных PostgreSQL
POSTGRES_PASSWORD=     # Пароль пользователя базы данных PostgreSQL
POSTGRES_HOST=         # Хост базы данных (в Docker: имя сервиса базы данных)
POSTGRES_PORT=         # Порт подключения к базе данных
POSTGRES_DB=           # Имя базы данных

# Настройки безопасности
SECRET_KEY=            # Секретный ключ для генерации токенов
ALGORITHM=             # Алгоритм шифрования (например, HS256)
ACCESS_TOKEN_EXPIRE_MINUTES=  # Время жизни токенов в минутах

# Настройки Telegram
TELEGRAM_TOKEN=        # Токен Telegram-бота для отправки уведомлений

# Настройки Redis
REDIS_HOST=            # Хост Redis (в Docker: имя сервиса Redis)
REDIS_PORT=            # Порт Redis
REDIS_DB=              # Номер базы данных Redis
REDIS_PASSWORD=        # Пароль для Redis (если установлен)

# Настройки Celery
CELERY_BROKER_URL=     # URL брокера задач Celery (обычно Redis)
CELERY_RESULT_BACKEND= # URL для хранения результатов задач Celery
```

# Установка и запуск

## Убедитесь, что у вас установлен Docker и Docker Compose

- Установите Docker: [Инструкция по установке Docker](https://docs.docker.com/get-docker/).
- Установите Docker Compose: [Инструкция по установке Docker Compose](https://docs.docker.com/compose/install/).

---

## Запуск через Docker Compose

1. Перейдите в директорию проекта, где находится `docker-compose.yml`.
2. Выполните команду для сборки и запуска контейнеров:

   ```bash
   docker-compose up --build

# Применение миграций базы данных

Для применения миграций базы данных выполните следующую команду:

```bash
docker-compose exec app alembic upgrade head
```

# API документация


После запуска приложение доступно по адресу:

**API документация:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Swagger UI** позволяет отправлять запросы и тестировать API.