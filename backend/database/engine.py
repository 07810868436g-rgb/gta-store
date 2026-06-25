import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Импортируем нашу базовую модель из файла models.py
from database.models import Base

# Загружаем секреты из .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gta_store_db")

# Формируем ссылку для подключения (обязательно с драйвером asyncpg)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Создаем движок (engine). echo=False отключает вывод каждого SQL-запроса в консоль
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем фабрику сессий — именно через session мы будем общаться с базой
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_models():
    """
    Создает все таблицы в базе данных (если их еще нет).
    Функция пройдется по файлу models.py и создаст таблицу game_keys.
    """
    async with engine.begin() as conn:
        # В реальных больших проектах используют Alembic для миграций,
        # но для старта create_all() — идеальный и быстрый вариант.
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы базы данных успешно инициализированы!")