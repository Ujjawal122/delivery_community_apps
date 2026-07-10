
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from app.config import settings

# ── Configure once at import time ─────────────────────────────────
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# Avatar constraints
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
_FOLDER = "delivery_community/avatars"


class CloudinaryService:

    @staticmethod
    async def upload_avatar(file: UploadFile, user_id: str) -> str:
       
        # ── Validate MIME type ─────────────────────────────────────
        if file.content_type not in _ALLOWED_MIME:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file.content_type}'. "
                       f"Allowed: jpeg, png, webp, gif.",
            )

        # ── Read and validate size ─────────────────────────────────
        contents = await file.read()
        if len(contents) > _MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Avatar file must be 5 MB or smaller.",
            )

        # ── Upload to Cloudinary ───────────────────────────────────
        try:
            result = cloudinary.uploader.upload(
                contents,
                public_id=f"{_FOLDER}/{user_id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    # Resize to 400×400, crop to face, convert to webp
                    {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                    {"format": "webp", "quality": "auto"},
                ],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudinary upload failed: {exc}",
            )

        return result["secure_url"]

    @staticmethod
    async def delete_avatar(user_id: str) -> None:
        """
        Delete the user's avatar from Cloudinary.
        Silently ignores 'not found' responses.
        """
        try:
            cloudinary.uploader.destroy(
                f"{_FOLDER}/{user_id}",
                resource_type="image",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudinary delete failed: {exc}",
            )
