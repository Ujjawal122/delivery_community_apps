# Import Base first, then every model so Alembic sees all tables
# when it does `from app.models import Base`

from .base import Base, TimestampMixin          # noqa: F401

from .user import User                          # noqa: F401
from .auth import RefreshToken, Notification    # noqa: F401
from .community import Community, CommunityMember, MemberRole  # noqa: F401
from .post import Post, PostVote, PostType, Comment, CommentVote, Bookmark  # noqa: F401
from .hazard import HazardReport, HazardImage, HazardVote      # noqa: F401
from .gate import Gate, GateReview                             # noqa: F401
from .chat import Conversation, ConversationMember, Message, ConversationType  # noqa: F401
from .follow import Follow                                     # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "RefreshToken",
    "Notification",
    "Community",
    "CommunityMember",
    "MemberRole",
    "Post",
    "PostVote",
    "PostType",
    "Comment",
    "CommentVote",
    "Bookmark",
    "HazardReport",
    "HazardImage",
    "HazardVote",
    "Gate",
    "GateReview",
    "Conversation",
    "ConversationMember",
    "Message",
    "ConversationType",
    "Follow",
]