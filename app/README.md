## Проект 

Есть проект создания хостинга сервисов VPS, разработки микросервисных приложений, n8n, хостинга ботов и контейнеров с автоматическим деплоем apps, AI-агентов. 
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
            └── ai_tasks.py    # AI-агенты
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
celery==5.3.4
redis==5.0.1
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