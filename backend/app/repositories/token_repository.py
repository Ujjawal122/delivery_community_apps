"""
app/repositories/token_repository.py
All database access for RefreshToken.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.models.auth import RefreshToken
from app.repositories.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.add(db_token)
        await self.flush()
        return db_token

    async def revoke(self, db_token: RefreshToken) -> None:
        """Mark a single token as revoked."""
        db_token.is_revoked = True
        await self.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke every active refresh token for a user (e.g. after password reset)."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        await self.flush()
