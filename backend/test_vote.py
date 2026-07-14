import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # 1. Login to get token
        login_resp = await client.post(
            "http://localhost:8000/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        if login_resp.status_code != 200:
            print("Login failed:", login_resp.text)
            # Register first
            reg_resp = await client.post(
                "http://localhost:8000/auth/register",
                json={"email": "test2@example.com", "password": "password123", "full_name": "Test User"}
            )
            login_resp = await client.post(
                "http://localhost:8000/auth/login",
                json={"email": "test2@example.com", "password": "password123"}
            )
        
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create a post
        post_resp = await client.post(
            "http://localhost:8000/posts",
            json={"title": "Test Post", "post_type": "share"},
            headers=headers
        )
        post_id = post_resp.json()["data"]["id"]
        print(f"Created post: {post_id}")
        
        # 3. Get post details initially
        get_resp = await client.get(f"http://localhost:8000/posts/{post_id}", headers=headers)
        data = get_resp.json()["data"]
        print(f"Initial -> Up: {data['upvotes_count']}, Down: {data['downvotes_count']}, Vote: {data['user_vote']}")
        
        # 4. Downvote the post (user has not upvoted)
        vote_resp = await client.post(
            f"http://localhost:8000/posts/{post_id}/vote",
            json={"vote_type": "down"},
            headers=headers
        )
        data = vote_resp.json()["data"]
        print(f"After Downvote -> Up: {data['upvotes_count']}, Down: {data['downvotes_count']}, Vote: {data['user_vote']}")
        
        # 5. Upvote the post (switch vote)
        vote_resp = await client.post(
            f"http://localhost:8000/posts/{post_id}/vote",
            json={"vote_type": "up"},
            headers=headers
        )
        data = vote_resp.json()["data"]
        print(f"After Switch to Upvote -> Up: {data['upvotes_count']}, Down: {data['downvotes_count']}, Vote: {data['user_vote']}")

if __name__ == "__main__":
    asyncio.run(main())
