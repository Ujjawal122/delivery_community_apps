"""
test_posts.py — End-to-end tests for all 16 post/comment endpoints.
Uses real DB, fake Redis, mocked email.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.exceptions import AppError, ForbiddenError, NotFoundError, BadRequestError
from app.models import *
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.post import CommentCreate, CommentUpdate, PostCreate, PostUpdate, VoteRequest
from app.services.auth_service import AuthService
from app.services.post_service import CommentService, PostService
from app.models.post import PostType

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

PASS = "[PASS]"
FAIL = "[FAIL]"
results: list[bool] = []


def ok(label, detail=""):
    print(f"  {PASS} {label}" + (f"  ({detail})" if detail else ""))
    results.append(True)


def fail(label, err):
    print(f"  {FAIL} {label}  ->  {err}")
    results.append(False)


class FakeRedis:
    _store: dict = {}
    async def ping(self): return True
    async def set(self, k, v, ex=None, **kw): self._store[k] = v; return True
    async def get(self, k): return self._store.get(k)
    async def delete(self, *keys):
        for k in keys: self._store.pop(k, None)
    async def exists(self, k): return 1 if k in self._store else 0
    async def incr(self, k):
        self._store[k] = str(int(self._store.get(k, "0")) + 1); return int(self._store[k])
    async def expire(self, k, ttl): return True
    async def sadd(self, k, *v): self._store.setdefault(k, set()); self._store[k].update(v)
    async def srem(self, k, *v): [self._store.get(k, set()).discard(i) for i in v]
    async def smembers(self, k): return set(self._store.get(k) or set())
    async def hset(self, k, mapping=None, **kw):
        self._store.setdefault(k, {}); mapping and self._store[k].update(mapping)
    async def hgetall(self, k): return dict(self._store.get(k) or {})
    async def zadd(self, k, m, **kw): self._store.setdefault(k, {}); self._store[k].update(m)
    async def zrem(self, k, *m):
        for i in m: self._store.get(k, {}).pop(i, None)
    async def zscore(self, k, m): return (self._store.get(k) or {}).get(m)
    async def zrange(self, k, s, e, **kw): return list((self._store.get(k) or {}).keys())
    async def zrevrange(self, k, s, e, withscores=False): return []
    async def zcount(self, k, mn, mx): return 0
    async def zremrangebyscore(self, k, mn, mx): pass
    async def zincrby(self, k, a, m): self._store.setdefault(k, {}); self._store[k][m] = self._store[k].get(m, 0) + a
    async def lpush(self, k, *v): self._store.setdefault(k, []); [self._store[k].insert(0, i) for i in v]
    async def ltrim(self, k, s, e): self._store[k] = (self._store.get(k) or [])[s:e+1]
    async def lrange(self, k, s, e): lst = self._store.get(k) or []; return lst[s:] if e == -1 else lst[s:e+1]
    async def llen(self, k): return len(self._store.get(k) or [])
    async def rpush(self, k, *v): self._store.setdefault(k, []); self._store[k].extend(v)
    async def blpop(self, k, timeout=0): return None
    async def info(self, s=None): return {}
    async def scan_iter(self, pattern="*"):
        import fnmatch
        for k in list(self._store.keys()):
            if fnmatch.fnmatch(k, pattern): yield k
    async def aclose(self): pass


async def run():
    redis = FakeRedis()
    email = f"posttest_{uuid.uuid4().hex[:8]}@example.com"
    email2 = f"posttest2_{uuid.uuid4().hex[:8]}@example.com"
    user = None
    user2 = None
    post_id = None
    comment_id = None

    # Setup: create two users (mark verified so login works)
    with patch("app.services.email_service.EmailService.send_verification_email", new_callable=AsyncMock):
        async with Session() as db:
            resp = await AuthService.register_user(db, redis, RegisterRequest(
                full_name="Post Tester", email=email, password="TestPass123!"))
            await db.commit()
            user = resp.user

        # Mark verified directly in DB
        async with Session() as db:
            await db.execute(
                text("UPDATE users SET is_verified = TRUE WHERE email = :e"), {"e": email}
            )
            await db.commit()

        async with Session() as db:
            tokens = await AuthService.login_user(db, redis, LoginRequest(
                email=email, password="TestPass123!"))
            await db.commit()

        async with Session() as db:
            resp2 = await AuthService.register_user(db, redis, RegisterRequest(
                full_name="Other User", email=email2, password="TestPass123!"))
            await db.commit()
            user2 = resp2.user

        async with Session() as db:
            await db.execute(
                text("UPDATE users SET is_verified = TRUE WHERE email = :e"), {"e": email2}
            )
            await db.commit()

    from app.repositories.user_repository import UserRepository
    async with Session() as db:
        user_repo = UserRepository(db)
        u = await user_repo.get_by_id(user.id)
        u2 = await user_repo.get_by_id(user2.id)

        # ── 1. Create post ─────────────────────────────────────
        print("\n-- 1. Create post --")
        try:
            result = await PostService.create_post(db, u, PostCreate(
                title="Test Question", content="What is the best route?",
                post_type=PostType.question,
            ))
            await db.commit()
            post_id = result.id
            assert result.post_type == PostType.question
            ok("create_post", f"id={post_id} type={result.post_type}")
        except Exception as e:
            fail("create_post", e); return

        # ── 2. Get single post ─────────────────────────────────
        print("\n-- 2. Get post --")
        async with Session() as db2:
            try:
                result = await PostService.get_post(db2, post_id)
                assert result.title == "Test Question"
                ok("get_post", f"title={result.title}")
            except Exception as e:
                fail("get_post", e)

        # ── 3. List posts ──────────────────────────────────────
        print("\n-- 3. List posts --")
        async with Session() as db2:
            try:
                result = await PostService.list_posts(db2, page=1, limit=20)
                assert result.total >= 1
                ok("list_posts", f"total={result.total}")
            except Exception as e:
                fail("list_posts", e)

        # ── 4. Filter by post_type ─────────────────────────────
        print("\n-- 4. Filter by post_type --")
        async with Session() as db2:
            try:
                result = await PostService.list_posts(db2, post_type=PostType.question)
                assert all(p.post_type == PostType.question for p in result.items)
                ok("list_posts_filter", f"all question posts: {result.total}")
            except Exception as e:
                fail("list_posts_filter", e)

        # ── 5. Update post ─────────────────────────────────────
        print("\n-- 5. Update post --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await PostService.update_post(db2, u_reload, post_id,
                    PostUpdate(title="Updated Title"))
                await db2.commit()
                assert result.title == "Updated Title"
                ok("update_post")
            except Exception as e:
                fail("update_post", e)

        # ── 6. Forbidden update by other user ──────────────────
        print("\n-- 6. Forbidden update --")
        async with Session() as db2:
            try:
                u2_reload = await UserRepository(db2).get_by_id(user2.id)
                await PostService.update_post(db2, u2_reload, post_id,
                    PostUpdate(title="Hacked"))
                fail("forbidden_update", "should have raised ForbiddenError")
            except (ForbiddenError, AppError) as e:
                ok("forbidden_update_correctly_rejected", f"type={type(e).__name__}")
            except Exception as e:
                fail("forbidden_update", e)

        # ── 7. Vote up ─────────────────────────────────────────
        print("\n-- 7. Vote up --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await PostService.vote_post(db2, u_reload, post_id, "up")
                await db2.commit()
                assert result.upvotes_count == 1
                ok("vote_up", f"upvotes={result.upvotes_count}")
            except Exception as e:
                fail("vote_up", e)

        # ── 8. Toggle vote off (same vote again) ───────────────
        print("\n-- 8. Toggle vote off --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await PostService.vote_post(db2, u_reload, post_id, "up")
                await db2.commit()
                assert result.upvotes_count == 0
                ok("toggle_vote_off", f"upvotes={result.upvotes_count}")
            except Exception as e:
                fail("toggle_vote_off", e)

        # ── 9. Vote down + switch to up ────────────────────────
        print("\n-- 9. Vote switch --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                await PostService.vote_post(db2, u_reload, post_id, "down")
                await db2.commit()
                result = await PostService.vote_post(db2, u_reload, post_id, "up")
                await db2.commit()
                assert result.upvotes_count == 1 and result.downvotes_count == 0
                ok("vote_switch", f"up={result.upvotes_count} down={result.downvotes_count}")
            except Exception as e:
                fail("vote_switch", e)

        # ── 10. Remove vote ────────────────────────────────────
        print("\n-- 10. Remove vote --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await PostService.remove_vote(db2, u_reload, post_id)
                await db2.commit()
                assert result.upvotes_count == 0
                ok("remove_vote")
            except Exception as e:
                fail("remove_vote", e)

        # ── 11. Bookmark toggle ────────────────────────────────
        print("\n-- 11. Bookmark toggle --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                r1 = await PostService.toggle_bookmark(db2, u_reload, post_id)
                await db2.commit()
                assert r1.bookmarked is True
                ok("bookmark_add")

                r2 = await PostService.toggle_bookmark(db2, u_reload, post_id)
                await db2.commit()
                assert r2.bookmarked is False
                ok("bookmark_remove")
            except Exception as e:
                fail("bookmark_toggle", e)

        # ── 12. Get bookmarks ──────────────────────────────────
        print("\n-- 12. Get bookmarks --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                # Add bookmark first
                await PostService.toggle_bookmark(db2, u_reload, post_id)
                await db2.commit()
                result = await PostService.get_bookmarks(db2, u_reload)
                assert result.total >= 1
                ok("get_bookmarks", f"total={result.total}")
                # Remove it
                await PostService.toggle_bookmark(db2, u_reload, post_id)
                await db2.commit()
            except Exception as e:
                fail("get_bookmarks", e)

        # ── 13. Create comment ─────────────────────────────────
        print("\n-- 13. Create comment --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await CommentService.create_comment(db2, u_reload, post_id,
                    CommentCreate(content="Great post!"))
                await db2.commit()
                comment_id = result.id
                assert result.content == "Great post!"
                ok("create_comment", f"id={comment_id}")
            except Exception as e:
                fail("create_comment", e); return

        # ── 14. Create reply ───────────────────────────────────
        print("\n-- 14. Create reply --")
        async with Session() as db2:
            try:
                u2_reload = await UserRepository(db2).get_by_id(user2.id)
                result = await CommentService.create_comment(db2, u2_reload, post_id,
                    CommentCreate(content="I agree!", parent_id=comment_id))
                await db2.commit()
                assert result.parent_id == comment_id
                ok("create_reply", f"parent_id={result.parent_id}")
            except Exception as e:
                fail("create_reply", e)

        # ── 15. List comments ──────────────────────────────────
        print("\n-- 15. List comments --")
        async with Session() as db2:
            try:
                comments = await CommentService.list_comments(db2, post_id)
                assert len(comments) >= 1
                assert len(comments[0].replies) >= 1
                ok("list_comments_with_replies",
                   f"{len(comments)} top-level, {len(comments[0].replies)} replies")
            except Exception as e:
                fail("list_comments", e)

        # ── 16. Update comment ─────────────────────────────────
        print("\n-- 16. Update comment --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await CommentService.update_comment(db2, u_reload,
                    comment_id, CommentUpdate(content="Updated comment"))
                await db2.commit()
                assert result.content == "Updated comment"
                ok("update_comment")
            except Exception as e:
                fail("update_comment", e)

        # ── 17. Vote on comment ────────────────────────────────
        print("\n-- 17. Vote comment --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await CommentService.vote_comment(db2, u_reload, comment_id, "up")
                await db2.commit()
                ok("vote_comment")
            except Exception as e:
                fail("vote_comment", e)

        # ── 18. Remove comment vote ────────────────────────────
        print("\n-- 18. Remove comment vote --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                result = await CommentService.remove_comment_vote(db2, u_reload, comment_id)
                await db2.commit()
                ok("remove_comment_vote")
            except Exception as e:
                fail("remove_comment_vote", e)

        # ── 19. Delete comment ─────────────────────────────────
        print("\n-- 19. Delete comment --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                await CommentService.delete_comment(db2, u_reload, comment_id)
                await db2.commit()
                ok("delete_comment")
            except Exception as e:
                fail("delete_comment", e)

        # ── 20. Delete post ────────────────────────────────────
        print("\n-- 20. Delete post --")
        async with Session() as db2:
            try:
                u_reload = await UserRepository(db2).get_by_id(user.id)
                await PostService.delete_post(db2, u_reload, post_id)
                await db2.commit()
                ok("delete_post")
            except Exception as e:
                fail("delete_post", e)

        # ── 21. Get deleted post → 404 ─────────────────────────
        print("\n-- 21. Get deleted post (expect 404) --")
        async with Session() as db2:
            try:
                await PostService.get_post(db2, post_id)
                fail("get_deleted_post", "should have raised NotFoundError")
            except (NotFoundError, AppError) as e:
                ok("get_deleted_post_404", f"type={type(e).__name__}")
            except Exception as e:
                fail("get_deleted_post", e)

    # Cleanup users
    print("\n-- Cleanup --")
    async with Session() as db2:
        try:
            await db2.execute(text("DELETE FROM users WHERE email IN (:e1, :e2)"),
                              {"e1": email, "e2": email2})
            await db2.commit()
            ok("cleanup")
        except Exception as e:
            fail("cleanup", e)

    await engine.dispose()


async def main():
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Community Module — End-to-End Test")
    print(sep)
    await run()
    passed = sum(results)
    total = len(results)
    print(f"\n{sep}")
    print(f"  Results: {passed}/{total} passed {'[ALL PASS]' if passed == total else '[SOME FAILED]'}")
    print(f"{sep}\n")


if __name__ == "__main__":
    asyncio.run(main())
