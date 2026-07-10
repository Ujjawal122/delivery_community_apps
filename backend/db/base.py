# This file is imported by alembic/env.py so that autogenerate
# can diff ALL tables against the live database.
# Do not remove any import — missing imports = missing migrations.

from app.models.base import Base  # noqa: F401 — re-exports declarative Base
from app.models import (          # noqa: F401 — registers every table on Base.metadata
    User,
    RefreshToken,
    Notification,
    Community,
    CommunityMember,
    MemberRole,
    Post,
    PostVote,
    Comment,
    CommentVote,
    HazardReport,
    HazardImage,
    HazardVote,
    Gate,
    GateReview,
)
