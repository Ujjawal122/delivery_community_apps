"""
app/cache/keys.py

Single source of truth for every Redis key pattern.
Import these instead of writing raw strings.

Naming convention:
  dc:{domain}:{identifier}

All functions return a str — ready to pass to redis commands.
"""


def refresh_token(token: str) -> str:
    """STRING  — stores user_id, TTL = REFRESH_TOKEN_TTL
    Lets us quickly validate a refresh token without hitting Postgres."""
    return f"dc:rt:{token}"


def access_token_blacklist(jti: str) -> str:
    """STRING  — exists = token is revoked.  TTL = remaining access token lifetime.
    Set on logout / password change / account delete."""
    return f"dc:blacklist:access:{jti}"


def email_verify_token(token: str) -> str:
    """STRING  — stores email address, TTL = EMAIL_VERIFY_TTL.
    Stateless JWT but we track usage to support single-use semantics."""
    return f"dc:email_verify:{token}"


def password_reset_token(token: str) -> str:
    """STRING  — stores email address, TTL = PASSWORD_RESET_TTL.
    Deleted on use so it can only be used once."""
    return f"dc:pwd_reset:{token}"


# ── Cache layer ────────────────────────────────────────────────────

def user_cache(user_id: str) -> str:
    """HASH    — full user profile fields, TTL = USER_CACHE_TTL."""
    return f"dc:cache:user:{user_id}"


def community_cache(community_id: str) -> str:
    """HASH    — community fields, TTL = COMMUNITY_CACHE_TTL."""
    return f"dc:cache:community:{community_id}"


def feed_cache(user_id: str, page: int = 1) -> str:
    """STRING (JSON)  — paginated feed list for a user, TTL = FEED_CACHE_TTL."""
    return f"dc:cache:feed:{user_id}:{page}"


# ── Trending ───────────────────────────────────────────────────────

def trending_posts() -> str:
    """SORTED SET  — member=post_id, score=engagement_score, TTL = TRENDING_TTL."""
    return "dc:trending:posts"


def trending_communities() -> str:
    """SORTED SET  — member=community_id, score=member_count+activity, TTL = TRENDING_TTL."""
    return "dc:trending:communities"


# ── Notifications & Jobs ───────────────────────────────────────────

def user_notifications(user_id: str) -> str:
    """LIST  — JSON-encoded notification objects, newest at head (LPUSH).
    Trimmed to last 100 on each push."""
    return f"dc:notifications:{user_id}"


def job_queue(queue_name: str) -> str:
    """LIST / STREAM  — background job queue.
    queue_name examples: 'email', 'push', 'resize'"""
    return f"dc:jobs:{queue_name}"


# ── Search ─────────────────────────────────────────────────────────

def search_suggestions(prefix: str) -> str:
    """SET   — members matching a search prefix (e.g. usernames, community names).
    One set per first 3 chars of query for efficient prefix lookup."""
    return f"dc:search:suggest:{prefix[:3].lower()}"


# ── Presence / Online ──────────────────────────────────────────────

def online_users() -> str:
    """SET   — member=user_id of all users active in last ONLINE_TTL seconds.
    Each user's entry refreshed on every API request (heartbeat)."""
    return "dc:online:users"


# ── Sessions ───────────────────────────────────────────────────────

def user_session(session_id: str) -> str:
    """HASH  — session metadata (user_id, device, ip, created_at).
    TTL = SESSION_TTL. Refreshed on each request."""
    return f"dc:session:{session_id}"


def user_session_index(user_id: str) -> str:
    """SET   — all active session_ids for a user.
    Used to enumerate / invalidate all sessions on logout-all."""
    return f"dc:session:user:{user_id}"


# ── Rate limiter ───────────────────────────────────────────────────

def rate_limit(identifier: str, action: str) -> str:
    """STRING (counter)  — incremented per request, TTL = RATE_LIMIT_TTL (window).
    identifier: IP address or user_id
    action:     route key, e.g. 'login', 'register', 'forgot_password'"""
    return f"dc:rl:{action}:{identifier}"
