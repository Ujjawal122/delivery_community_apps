from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

engine=create_async_engine(settings.DATABASE_URL, echo=True, future=True)

AsyncSessionLocal=async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)