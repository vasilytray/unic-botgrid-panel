# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.logger import app_logger as logger
from app.tasks.log_cleanup_task import log_cleanup
from app.tasks.background_tasks import background_tasks
import asyncio

# Импортируем все необходимое
from app.database import engine, async_session_maker
from app.models.relationships import configure_relationships


# # Импортируем ВСЕ модели
from app.users.models import User, UserLog
from app.roles.models import Role
from app.services.models import Service, BillingPlan
from app.billing.models import Invoice, Transaction

# Импортируем роутеры
from app.students.router import router as router_students
from app.majors.router import router as router_majors

from app.users.router import router as router_users
from app.roles.router import router as router_roles
from app.pages.router import router as router_pages
from app.lk.router import router as router_lk
from app.partials.router import router as partials_router
from app.tickets.router import router as router_ticket
from app.services.router import router as router_services
from app.monitoring.router import router as router_monitoring
from app.billing.router import router as router_billing
# from app.chat.router import router as chat_router

from app.exceptions import TokenExpiredException, TokenNoFoundException

async def startup():
    """Код, выполняемый при запуске приложения"""
    print("🚀 Запуск приложения Хостинг Провайдер...")
    
    # Настраиваем отношения между моделями
    configure_relationships()
    
    # Проверяем подключение к базе данных
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: print("✅ Подключение к базе данных установлено"))
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        raise
    
    # Проверяем зарегистрированные таблицы
    from app.database import Base
    tables = Base.metadata.tables
    print(f"✅ Зарегистрировано таблиц: {len(tables)}")
    
    print("✅ Приложение успешно запущено")

async def shutdown():
    """Код, выполняемый при остановке приложения"""
    print("🛑 Остановка приложения Хостинг Провайдер...")
    
    # Закрываем соединения с базой данных
    await engine.dispose()
    print("✅ Соединения с базой данных закрыты")

@asynccontextmanager
async def lifespan(app: FastAPI):
       # Startup
    logger.info("🚀 Starting FastAPI application...")
    
    try:
        # Запускаем фоновую задачу очистки логов
        asyncio.create_task(log_cleanup.start_periodic_cleanup())
        logger.info("✅ Фоновая задача очистки логов запущена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске фоновых задач: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    log_cleanup.is_running = False
    logger.info("✅ Фоновая задача очистки логов остановлена")


app = FastAPI(
    title="DokuHost",
    description="Панель управления VPS, Docker-контейнерами, ботами и n8n инстансами",
    version="1.0.0",
    lifespan=lifespan
)

app.mount('/static', StaticFiles(directory='app/static'), 'static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)



# @app.get("/") # эндпоинт главной страницы
# def home_page():
#     """API эндпоинт для получения информации о приложении"""
#     return {
#         "message": "Хостинг Провайдер API", 
#         "docs": "/docs",
#         "version": "1.0.0"
#     }

# @app.get("/auth")
# async def redirect_to_auth():
#     return RedirectResponse(url="/users/")



# Подключаем роутеры
app.include_router(router_pages)  # Должен быть первым, т.к. содержит эндпоинт /
app.include_router(partials_router)   # Добавляем роутер частичных страниц
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(lk.router, prefix="/lk", tags=["Personal Cabinet"])
app.include_router(router_lk)
app.include_router(router_users)
app.include_router(router_ticket)
app.include_router(router_services)
app.include_router(router_billing)
app.include_router(router_students)
app.include_router(router_majors)
app.include_router(router_roles)
# app.include_router(chat_router)

# Обработчик для TokenExpired
@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: HTTPException):
    # Возвращаем редирект на страницу /auth
    return RedirectResponse(url="/auth")

# Обработчик для TokenNoFound
@app.exception_handler(TokenNoFoundException)
async def token_no_found_exception_handler(request: Request, exc: HTTPException):
    # Возвращаем редирект на страницу /auth
    return RedirectResponse(url="/auth")

@app.get("/api")
async def api_root():
    """API эндпоинт для корневого пути"""
    return {
        "message": "Хостинг Провайдер API", 
        "docs": "/docs",
        "version": "1.0.0"
    }

# Health check эндпоинт
@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "message": "Хостинг Провайдер работает корректно"
    }