# Создание собственного API на Python (FastAPI) 
(повторение туториалов от [Yakovenko Oleksii](https://github.com/Yakvenalex))
1. [Создание собственного API на Python (FastAPI): Знакомство и первые функции](https://habr.com/ru/companies/amvera/articles/826196/)
2. [Создание собственного API на Python (FastAPI): Гайд по POST, PUT, DELETE запросам и моделям Pydantic](https://habr.com/ru/articles/827134/)

## Знакомство и первые функции
### Установка зависимостей

```
pip install -r requirements.txt
```

### Подготовка
1. Развернем базу данных в PostgreSQL локально в Docker - контейнере.
1.1. Поставим [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2.2. Создадим в корне проекта  файл docker-compose.yml 

```yml
version: '3.9'

services:
  postgres:
    image: postgres:latest
    container_name: postgres_container
    environment:
      POSTGRES_USER: amin
      POSTGRES_PASSWORD: my_super_password
      POSTGRES_DB: fast_api
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5430:5432"
    volumes:
      - ./pgdata:/var/lib/postgresql/data/pgdata
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    command: >
      postgres -c max_connections=1000
               -c shared_buffers=256MB
               -c effective_cache_size=768MB
               -c maintenance_work_mem=64MB
               -c checkpoint_completion_target=0.7
               -c wal_buffers=16MB
               -c default_statistics_target=100
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U postgres_user -d postgres_db" ]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    tty: true
    stdin_open: true

volumes:
  pgdata:
    driver: local
```
#### Краткий обзор Docker Compose файла

1. services/postgres:

**image**: используемая Docker-образ PostgreSQL, в данном случае postgres:latest.

**container_name**: имя контейнера, в котором будет запущен PostgreSQL.

**environment**: переменные окружения для настройки PostgreSQL (пользователь, пароль, имя базы данных - не забудьте указать свои).

**ports**: проброс портов, где "5430:5432" означает, что порт PostgreSQL внутри контейнера (5432) проброшен на порт хоста (5430). Это значит что для подключения к постгрес нужно будет прописывать порт 5430.

**volumes**: монтируем локальный каталог ``./pgdata`` внутрь контейнера для сохранения данных PostgreSQL.

**deploy**: определяет ресурсы и стратегию развертывания для Docker Swarm (необязательно для стандартного использования Docker Compose).

**command**: дополнительные параметры командной строки PostgreSQL для настройки параметров производительности.

**healthcheck**: проверка состояния PostgreSQL с использованием pg_isready.

***restart, tty, stdin_open***: настройки перезапуска контейнера и взаимодействия с ним через терминал.

2. volumes/pgdata:

Определяет том **pgdata**, который используется для постоянного хранения данных PostgreSQL.

#### Запуск PostgreSQL

- Запустим Docker Desktop

- Выполняем команду 

```sh
docker compose up -d
```

Эта команда запустит контейнер PostgreSQL в фоновом режиме **(-d)** на основе настроек, указанных в файле ``docker-compose.yml``

```sh
docker compose up -d
time="2025-02-26T19:24:11+07:00" level=warning msg="C:\\www\\pyfapi\\unic\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] Running 15/15
 ✔ postgres Pulled                                                                                                                          27.6s 
[+] Running 3/3
 ✔ Network unic_default         Created                                                                                                      0.2s 
 ✔ Volume "unic_pgdata"         Created                                                                                                      0.0s 
 ✔ Container postgres_fast_api  Started
```

Контейнер запущен и работает, подключемся к нему клиентом PgAdmin4 или DBeaver
указав данные базы и порт 5433 (мы выбрали его в настройках docker-compose.yml) в качестве порта для подключения к контейнеру

## Проект ---

Есть проект создания панели управления сервисов хостинга. 
1. Основа - FastAPI. 
2. ПРоект придерживается принципов The twelve-factor app is a methodology for building software-as-a-service apps: https://12factor.net/
3. В качестве сторонего сервиса БД - PostgrSQL
4. В качестве единой точки для операций с БД (абстрактный интерфейс для работы с persistence-хранилищем (БД, API, файлы)) используется app.dao.base.py
5. в качестве система логирования используется loguru
6. В качестве динамических credentials используются JWT - необходимо либо перейти на OAuth2 с Password Flow, либо дополнить систему на основе ACCESS_TOKEN_EXPIRE_MINUTES и 
REFRESH_TOKEN_EXPIRE_DAYS 
7. Все секреты хранятся в переменных окружения.
8. FrontEnd построен на принципах:
 - ✅ 1. Используем технологии SSR.
 - ✅ 2. В Панели управления используем полностью динамическую SPA-архитектуру с:
    - ✅ Адаптивным бургер-меню
    - ✅ Сеткой 1fr слева/справа
    - ✅ Фиксированной шириной сайдбара 256px
    - ✅ Динамическими модулями вместо перезагрузки страниц
    - ✅ Активными состояниями пунктов меню
    - ✅ Ленивой загрузкой контента
 - ✅ 3. Кнопки работают через единую систему обработки событий
 - ✅ 4. Ленивая загрузка модулей - контент загружается только при первом обращении
 - ✅ 5. Отдельный роутер для частичных страниц без дублирования кода
    - ✅ Частичные страницы для всех модулей Панели управления
    - ✅ Базовый шаблон для единообразного стиля частичных страниц 
 - Все частичные страницы доступны по пути /partials/* и загружаться динамически в основной контент! 🚀
 - Интеграция с существующей аутентификацией и системой ролей 🚀
 - Разделение на пользовательскую и админскую части 🚀
 - API для фронтенда с пагинацией и фильтрацией 🚀
 - Все работает как единое приложение без перезагрузок! 🚀

## Зависимости проекта

- `fastapi[all]==0.118.0`   - высокопроизводительный веб-фреймворк
- `pydantic==2.11.9`        - валидация данных
- `pydantic-settings==2.11.0` - библиотека для хранения настроек
- `jinja2==3.1.6`           - шаблонизатор
- `SQLAlchemy==2.0.43 `     - ORM для работы с базами данных
- `asyncpg==0.30.0`         - асинхронная поддержка для PostgreSQL
- `alembic==1.16.5`         - управление миграциями базы данных
- `loguru==0.7.3`           - красивое и удобное логирование
- `uvicorn==0.37.0`         - ASGI-сервер
- `httpx==0.28.1`
- `python-jose`
- `bcrypt==4.0.1`
- `libpass==1.9.2`
- `websockets==15.0.1`

## Структура проекта

Проект построен с учётом модульной архитектуры, что позволяет легко расширять приложение и упрощает его поддержку.
Каждый модуль отвечает за отдельные задачи, такие как авторизация или управление данными.

### Структура проекта (древо)



```
└── 📁app
    └── 📁.ideas
        └── 📁ticketsystem_by_Viy
            ├── app.js
            ├── index.html
            ├── style.css
        ├── messenger by_Viy.zip
        ├── readme.md
        ├── ticketsystem_by_Viy.zip
    └── 📁billing
        ├── dao.py
        ├── models.py
        ├── router.py
    └── 📁chat
        ├── dao.py
        ├── models.py
        ├── router.py
        ├── schemas.py
    └── 📁dao
        ├── base.py
    └── 📁lk
        ├── router.py
    └── 📁migration
        ├── env.py
        ├── README
        ├── script.py.mako
    └── 📁models
        ├── relationships.py
    └── 📁monitoring
        ├── router.py
    └── 📁pages
        ├── router.py
    └── 📁partials
        ├── router.py
    └── 📁roles
        ├── dao.py
        ├── dependencies.py
        ├── models.py
        ├── rb.py
        ├── router_old.py
        ├── router.py
        ├── schemas.py
    └── 📁services
        ├── dao.py
        ├── models.py
        ├── router.py
        ├── schemas.py
    └── 📁static
        └── 📁images
            ├── 2.webp
            ├── 4.webp
            ├── 5.webp
            ├── favicon.svg
            ├── icon.png
        └── 📁js
            ├── auth.js
            ├── chat.js
            ├── main.js
            ├── profile-edit.js
            ├── script.js
            ├── ticket.js
        └── 📁style
            ├── auth.css
            ├── chat.css
            ├── main_aside.css
            ├── main.css
            ├── profile-edit.css
            ├── profile.css
            ├── register.css
            ├── student.css
            ├── styles.css
            ├── ticket.css
        └── 📁uploads
            └── 📁tickets
    └── 📁tasks
        ├── background_tasks.py
        ├── log_cleanup_task.py
    └── 📁templates
        └── 📁partials
            ├── admin_ticket_request.html
            ├── admin_tickets.html
            ├── base.html
            ├── edit_basic_profile.html
            ├── edit_password.html
            ├── edit_profile.html
            ├── edit_security.html
            ├── profile_old.html
            ├── profile_simple.html
            ├── profile.html
            ├── user_tickets_old.html
            ├── user_tickets.html
        ├── auth.html
        ├── chat.html
        ├── dashboard_old.html
        ├── dashboard.html
        ├── dashboard25.html
        ├── debug_partials.html
        ├── index.html
        ├── login_form.html
        ├── main.html
        ├── my_invoices.html
        ├── my_services.html
        ├── profile.html
        ├── register_form.html
        ├── servicesdb.html
        ├── student.html
        ├── students.html
        ├── ticket.html
    └── 📁tickets
        ├── dao.py
        ├── models.py
        ├── router.py
        ├── schemas.py
    └── 📁users
        ├── auth.py
        ├── dao.py
        ├── dependencies.py
        ├── ip_dao.py
        ├── log_cleaner.py
        ├── models.py
        ├── rb.py
        ├── router.py
        ├── schemas.py
    └── 📁utils
        ├── datetime_utils.py
        ├── phone_parser.py
        ├── secutils.py
    └── 📁verificationcodes
        ├── dao.py
        ├── models.py
    ├── config.py
    ├── database.py
    ├── exceptions.py
    ├── logger.py
    ├── main.py
    ├── Project_structure_today.md
    └── README.md

```
## Требуется:
1. ### Получить FastAPI+Celery
Интеграция в проект FastAPI распределенной обработки задач Celery (в какой части необходимо доработать и/или переработать проект?) если проанализировать Древо структуры проектов, то где необходимо внести изменения для внедрения Celery.

## План выполнения задачи 
Анализируя структуру вашего проекта, вот где и как нужно внедрить Celery для распределенной обработки задач:

### 1. 📁 НОВЫЕ ПАПКИ И ФАЙЛЫ

```
└── 📁app
    └── 📁celery
        ├── __init__.py
        ├── config.py          # Конфигурация Celery
        ├── worker.py          # Инициализация Celery app
        └── 📁tasks
            ├── __init__.py
            ├── base.py        # Базовые задачи
            ├── email_tasks.py # Email рассылки
            ├── billing_tasks.py # Биллинг операции
            ├── deployment_tasks.py # Деплой сервисов
            ├── monitoring_tasks.py # Мониторинг
            ├── ai_tasks.py    # AI-агенты
            └── user_tasks.py
```

### 2. 🔧 ИЗМЕНЕНИЯ В СУЩЕСТВУЮЩИХ ФАЙЛАХ

#### `app/config.py` - добавить настройки Celery:
```python
class Settings(BaseSettings):
    # Существующие настройки...
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
```

#### `app/main.py` - инициализация Celery:
```python
from app.celery.worker import celery_app

@app.on_event("startup")
async def startup_event():
    # Существующий код...
    celery_app.conf.update(app.state.settings.dict())
```

### 3. 📝 ПЕРЕРАБОТКА СУЩЕСТВУЮЩИХ МОДУЛЕЙ

#### `app/tasks/` - ПЕРЕИМЕНОВАТЬ И ПЕРЕРАБОТАТЬ:
```
└── 📁app
    └── 📁tasks_old           # Старые синхронные задачи
    └── 📁async_tasks         # Новые асинхронные задачи (если нужны)
```

#### `app/billing/router.py` - пример интеграции:
```python
from app.celery.tasks.billing_tasks import process_payment_task

@router.post("/payments/")
async def create_payment(payment_data: PaymentSchema):
    # Сохраняем в БД
    payment = await BillingDAO.create_payment(payment_data)
    
    # Запускаем асинхронную обработку
    process_payment_task.delay(payment.id)
    
    return {"status": "processing", "task_id": task.id}
```

#### `app/services/router.py` - для деплоя:
```python
from app.celery.tasks.deployment_tasks import deploy_service_task

@router.post("/deploy/")
async def deploy_service(service_data: ServiceDeploySchema):
    task = deploy_service_task.delay(service_data.dict())
    return {"task_id": task.id, "status": "deploying"}
```

### 4. 🎯 КОНКРЕТНЫЕ ОБЛАСТИ ДЛЯ Celery:

#### **ВЫСОКОПРИОРИТЕТНЫЕ:**
1. **`app/billing/`** - обработка платежей, инвойсов
2. **`app/services/`** - деплой VPS/контейнеров
3. **`app/monitoring/`** - периодические проверки сервисов
4. **`app/chat/`** - обработка AI-агентов, тяжелые вычисления

#### **СРЕДНИЙ ПРИОРИТЕТ:**
5. **`app/users/`** - отправка email, верификация
6. **`app/tickets/`** - уведомления, автоматические ответы

#### **НИЗКИЙ ПРИОРИТЕТ:**
7. **`app/tasks/background_tasks.py`** - ПЕРЕНОС в Celery tasks
8. **`app/tasks/log_cleanup_task.py`** - ПЕРЕНОС в периодические задачи Celery

### 5. 🚀 КАК ИНТЕГРИРОВАТЬ:

#### Шаг 1: Создать базовую структуру Celery
```python
# app/celery/worker.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
```

#### Шаг 2: Перенести существующие фоновые задачи
```python
# app/celery/tasks/billing_tasks.py
@celery_app.task
def process_payment_task(payment_id: int):
    # Логика обработки платежа
    pass
```

#### Шаг 3: Обновить роутеры для использования Celery
Заменить прямые вызовы на `.delay()` или `.apply_async()`

### 6. 📊 КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ:

1. **ЗАВИСИМОСТИ** - добавить в `requirements.txt`:
```
celery==5.5.3
redis==7.0.1
flower==2.0.1  # для мониторинга
```

2. **DOCKER** - добавить сервисы в `docker-compose.yml`:
```yaml
services:
  redis:
    image: redis:7-alpine
    
  celery_worker:
    build: .
    command: celery -A app.celery.worker worker --loglevel=info
    
  celery_beat:
    build: .
    command: celery -A app.celery.worker beat --loglevel=info
    
  flower:
    build: .
    command: celery -A app.celery.worker flower --port=5555
```

3. **DEPENDENCIES** - обновить импорты во всех модулях, где используются фоновые задачи

### 7. 🎪 ПРЕИМУЩЕСТВА ДЛЯ ВАШЕГО ПРОЕКТА:

- **Масштабируемость** - можно запускать несколько воркеров для VPS/контейнеров
- **Надежность** - retry механизм для деплоя сервисов
- **Мониторинг** - Flower для отслеживания задач AI-агентов
- **Производительность** - освобождение FastAPI для API запросов

**Рекомендую начинать с billing и services модулей** - это даст максимальный эффект для вашего хостинга VPS и микросервисов! 🚀 

## Микросервисы и сторонние службы

Проект разделен на микросервисы и сторонние службы. **Сторонняя служба**– это любая служба, которая доступна приложению по сети и необходима как часть его нормальной работы.

Создадим модульную структуру с раздельными docker-compose файлами. Вот предлагаемая структура:

### 📁 СТРУКТУРА ПРОЕКТА

```
project-root/
├── 📁 app/                          # Основное приложение (существующее)
│   ├── 📁 celery/                   # Конфигурация Celery
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── worker.py
│   │   └── 📁 tasks/                # Задачи Celery
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── user_tasks.py
│   │       ├── ticket_tasks.py
│   │       └── monitoring_tasks.py
│   ├── 📁 users/                    # Модуль пользователей
│   ├── 📁 tickets/                  # Тикет-система
│   ├── 📁 roles/                    # Роли и права
│   ├── 📁 templates/                # Шаблоны
│   ├── 📁 static/                   # Статические файлы
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── ... [остальные существующие файлы]
│
├── 📁 postgres/                     # Конфигурация PostgreSQL (НОВОЕ)
│   ├── docker-compose.yml           # Конфиг только для Postgres
│   └── 📁 init/                     # SQL скрипты инициализации
│       ├── 01-init.sql
│       └── 02-seed-data.sql
│
├── 📁 redis/                        # Конфигурация Redis (НОВОЕ)
│   └── docker-compose.yml           # Конфиг только для Redis
│
├── 📁 monitoring/                   # Мониторинг (НОВОЕ - опционально)
│   └── docker-compose.yml           # Для Prometheus/Grafana
│
├── Dockerfile                       # ОБЩИЙ ДЛЯ ВСЕХ СЕРВИСОВ (НОВОЕ)
├── docker-compose.yml               # ОСНОВНОЙ КОМПОЗ-ФАЙЛ (НОВОЕ)
├── requirements.txt                 # Зависимости Python
├── .env                            # Переменные окружения
├── .dockerignore                   # Исключения для Docker
└── README.md
```

## 🎯 КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ

```bash
# Запуск всех сервисов
docker compose up -d

# Запуск только базы данных  и redis
docker compose up -d postgres redis

# Запуск только  redis
docker compose up -d redis

# Запуск только приложения
docker compose up -d app

# Запуск только Celery
docker compose up -d celery_worker celery_beat

# Просмотр логов конкретного сервиса
docker compose logs app
docker compose logs celery_worker -f

# Остановка сервисов
docker compose stop app
docker compose stop celery_worker celery_beat

# Полная пересборка
docker compose down && docker compose up -d --build

# Перезапустите Redis
docker compose restart redis

# Полная пересборка Redis
docker compose down redis
docker compose up -d redis

# Проверка аутентификации
docker compose exec redis redis-cli -a _you_default_redis_pass_ ping
# Должен вернуть: PONG

# Проверка без пароля (должен отказать)
docker compose exec redis redis-cli ping
# Должен вернуть: NOAUTH Authentication required

# Проверка с пользователем Celery
docker compose exec redis redis-cli -u redis://celery_user:celery_password_123@localhost:6379 ping

```

🚀 ПРЕИМУЩЕСТВА:
- Config.py управляет URL - как и задумано в вашем приложении
- Docker-compose только передает параметры - не занимается логикой
- Легко тестировать - можно подменить отдельные параметры
- Следует принципам 12-factor app - конфигурация через environment variables
- Оставляйте генерацию DATABASE_URL в config.py - это правильный подход! 🎉

🔧 ПРОВЕРКА ИМЕН КОНТЕЙНЕРОВ
bash
# Посмотрите точные имена контейнеров
docker compose ps

# Пример вывода:
# NAME                  COMMAND                  SERVICE             ...
# postgres_fast_api     "docker-entrypoint.s…"   postgres           ...
# redis_container       "docker-entrypoint.s…"   redis              ...
# fastapi_app           "uvicorn app.main:ap…"   app                ...

🐳 КАК РАБОТАЕТ DOCKER СЕТЬ
text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   fastapi_app   │────│   app_network    │────│ postgres_fast_api│
│                 │    │                  │    │                 │
│ DB_HOST=        │    │ DNS Resolution:  │    │ Listens on:     │
│ postgres_fast_api│───│ postgres_fast_api│───▶│ 0.0.0.0:5432    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ
bash
# Проверьте что app видит postgres по имени
docker compose exec app ping postgres_fast_api

# Проверьте доступность порта
docker compose exec app nc -zv postgres_fast_api 5432

# Проверьте переменные в контейнере
docker compose exec app env | grep DB