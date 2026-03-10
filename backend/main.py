"""
Главный файл FastAPI приложения
"""
import os
import sys
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger

from .storage.prompt_store import PromptStore
from .ai.model_provider import ModelFactory
from .ai.anthropic_provider import AnthropicProvider
from .ai.browser_use_model import BrowserUseProvider
from .core.agent_manager import AgentManager
from .api.routes import get_all_routers, init_routes
from .api.websocket import websocket_endpoint, setup_websocket_callbacks


# Загружаем переменные окружения
load_dotenv()

# Настройка loguru
logger.remove()  # Удаляем стандартный хэндлер
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/backend.log",
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Создаем FastAPI приложение
app = FastAPI(
    title="Browser Automation System",
    description="Самообучающаяся система автоматизации браузера на базе browser-use",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные объекты
prompt_store: PromptStore = None
agent_manager: AgentManager = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global prompt_store, agent_manager
    
    # Получаем API ключи из переменных окружения
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not anthropic_api_key:
        logger.warning("⚠️  ANTHROPIC_API_KEY не установлен!")

    # Инициализируем хранилище
    data_dir = os.getenv("DATA_DIR", "data")
    prompt_store = PromptStore(data_dir=data_dir)
    logger.info(f"📁 Директория данных: {data_dir}")

    # Создаем AI провайдеры
    analysis_provider = ModelFactory.create_provider(
        "anthropic",
        api_key=anthropic_api_key,
        model_name="claude-sonnet-4-20250514"
    )
    logger.info("🤖 AI модель для анализа: Claude Sonnet 4")

    execution_provider = ModelFactory.create_provider(
        "browser-use",
        api_key=anthropic_api_key
    )
    logger.info("🎯 AI модель для выполнения: browser-use + Claude Sonnet 4")

    # Создаем менеджер агентов
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    agent_manager = AgentManager(
        store=prompt_store,
        analysis_provider=analysis_provider,
        execution_provider=execution_provider,
        headless=headless
    )
    logger.info(f"🌐 Headless режим: {headless}")

    # Инициализируем роуты
    init_routes(agent_manager, prompt_store)

    # Настраиваем WebSocket колбэки
    setup_websocket_callbacks(agent_manager)

    logger.success("✅ Backend инициализирован успешно!")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    logger.info("🛑 Остановка сервера...")


# Подключаем роуты
for router in get_all_routers():
    app.include_router(router)


# WebSocket endpoint
@app.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    """WebSocket для конкретной задачи"""
    await websocket_endpoint(websocket, task_id)


@app.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Глобальный WebSocket для всех событий"""
    await websocket_endpoint(websocket)


# Health check
@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "ai_provider": "Anthropic Claude",
        "browser_automation": "browser-use"
    }


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Browser Automation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
