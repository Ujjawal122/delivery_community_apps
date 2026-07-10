"""
app/repositories/user_repository.py
All database access for the User model.
"""

import uuid

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    # ── Lookups ────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:  # type: ignore[override]
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def email_taken_by_other(self, email: str, exclude_id: uuid.UUID) -> bool:
        """Returns True if the email is already registered to a *different* user."""
        result = await self.db.execute(
            select(User).where(User.email == email, User.id != exclude_id)
        )
        return result.scalar_one_or_none() is not None

    # ── Writes ─────────────────────────────────────────────────────

    async def create(
        self,
        *,
        full_name: str,
        email: str,
        hashed_password: str,
        phone_number: str | None = None,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            password=hashed_password,
            phone_number=phone_number,
        )
        self.add(user)
        await self.flush()
        await self.refresh(user)
        return user
