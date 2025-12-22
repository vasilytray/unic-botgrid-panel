# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import time
import asyncio

# Явные импорты (без __init__.py)
from app.core.config import get_settings
from app.core.database import database_manager, get_db
from app.core.redis import redis_manager
from app.core.rabbitmq import rabbitmq_manager
from app.core.exceptions import (
    TokenExpiredException, 
    TokenNotFoundException, 
    UserAlreadyExistsException,
    UserNotFoundException, 
    InvalidCredentialsException,
    InsufficientPermissionsException,
    ValidationException,
    ResourceNotFoundException,
    RedisConnectionException,
    DatabaseConnectionException
)

from app.services.centrifugo_service import centrifugo_service
from app.utils.logging import get_logger
from app.tasks.log_cleanup_task import log_cleanup
from app.tasks.background_tasks import background_tasks
from fastapi.templating import Jinja2Templates

from app.models.relationships import configure_relationships

# Импорты моделей
from app.models.users import User, UserLog
from app.models.roles import Role
from app.services.models import Service, BillingPlan
from app.billing.models import Invoice, Transaction

# Импорты роутеров
from app.students.router import router as router_students
from app.majors.router import router as router_majors
from app.api.v1.users import router as router_users
from app.api.v1.roles import router as router_roles
from app.pages.router import router as router_pages
from app.lk.router import router as router_lk
from app.partials.router import router as partials_router
from app.tickets.router import router as router_ticket
from app.services.router import router as router_services
from app.monitoring.router import router as router_monitoring
from app.billing.router import router as router_billing

# Настройка логирования
logger = get_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для управления жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Starting FastAPI application...")
    
    try:
        # Настраиваем отношения между моделями
        configure_relationships()
        
        # Запускаем фоновую задачу очистки логов
        asyncio.create_task(log_cleanup.start_periodic_cleanup())
        logger.info("✅ Фоновая задача очистки логов запущена")
        
        # Инициализация базы данных
        await database_manager.init_database()
        logger.info("✅ Database initialized")
        
        # Инициализация переменных для обратной совместимости
        init_compatibility_variables()
        logger.info("✅ Database compatibility variables initialized")
        
        # Инициализация Redis
        await redis_manager.init_redis()
        logger.info("✅ Redis initialized")
        
        # Инициализация RabbitMQ (для FastStream workers)
        await rabbitmq_manager.init_broker()
        logger.info("✅ RabbitMQ initialized")
        
        logger.info("✅ Centrifugo service ready")
        logger.info(f"🎯 Application started in {settings.ENVIRONMENT} mode")
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise
    
    yield  # Приложение работает здесь
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    try:
        log_cleanup.is_running = False
        logger.info("✅ Фоновая задача очистки логов остановлена")
        
        await redis_manager.close()
        logger.info("✅ Redis connections closed")
        
        await database_manager.close()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Application shutdown error: {e}")
    
    logger.info("👋 Application shutdown complete")

app = FastAPI(
    title="DokuHost",
    description="Панель управления VPS, Docker-контейнерами, ботами и n8n инстансами",
    version="1.0.0",
    lifespan=lifespan
)

# Статические файлы
app.mount('/static', StaticFiles(directory='app/static'), 'static')
templates = Jinja2Templates(directory="app/templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(router_pages)
app.include_router(partials_router)
app.include_router(router_lk)
app.include_router(router_users)
app.include_router(router_ticket)
app.include_router(router_services)
app.include_router(router_billing)
app.include_router(router_students)
app.include_router(router_majors)
app.include_router(router_roles)

# Обработчики исключений
@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: TokenExpiredException):
    return RedirectResponse(url="/auth")

@app.exception_handler(TokenNotFoundException)
async def token_no_found_exception_handler(request: Request, exc: TokenNotFoundException):
    return RedirectResponse(url="/auth")

@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    logger.warning(f"❌ User not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Health check эндпоинт
@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    try:
        # Проверка базы данных
        db_healthy = await database_manager.health_check()
        health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Проверка Redis
        redis = await redis_manager.get_redis()
        await redis.ping() # type: ignore
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.on_event("startup")
async def startup_event():
    await database_manager.init_database()

@app.get("/")
async def root():
    return {
        "message": "Docker Hosting Panel API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/api")
async def api_root():
    return {
        "message": "Хостинг Провайдер API", 
        "docs": "/docs",
        "version": "1.0.0"
    }