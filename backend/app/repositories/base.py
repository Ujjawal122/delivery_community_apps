"""
app/repositories/base.py
Generic async repository — provides common CRUD operations.
All model-specific repositories inherit from this.

Usage:
    class UserRepository(BaseRepository[User]):
        model = User
"""

from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Provides:
      get_by_id   — fetch by primary key
      get_all     — paginated list
      add         — stage a new model instance
      delete      — delete a model instance
    """

    model: Type[ModelT]  # subclasses must set this

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, pk: Any) -> ModelT | None:
        """Return a single row by primary key, or None."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == pk)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[ModelT]:
        """Return a paginated list of all rows."""
        result = await self.db.execute(
            select(self.model).offset(offset).limit(limit)  # type: ignore[attr-defined]
        )
        return result.scalars().all()

    def add(self, instance: ModelT) -> ModelT:
        """Stage a new record (call db.flush() / db.commit() after)."""
        self.db.add(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """Delete a record (call db.flush() / db.commit() after)."""
        await self.db.delete(instance)

    async def flush(self) -> None:
        await self.db.flush()

    async def refresh(self, instance: ModelT) -> None:
        await self.db.refresh(instance)
