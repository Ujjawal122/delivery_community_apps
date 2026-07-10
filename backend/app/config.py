from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
  
    DATABASE_URL: str = ""

  
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    FRONTEND_URL: str = "http://localhost:3000"

   
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

  
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_USE_TLS: bool = True          # always True for Redis Cloud
    REDIS_MAX_CONNECTIONS: int = 20

   
    REDIS_REFRESH_TOKEN_TTL: int = 7 * 24 * 3600      
    REDIS_ACCESS_TOKEN_BLACKLIST_TTL: int = 30 * 60   
    REDIS_EMAIL_VERIFY_TTL: int = 24 * 3600            
    REDIS_PASSWORD_RESET_TTL: int = 3600              
    REDIS_USER_CACHE_TTL: int = 300                    
    REDIS_COMMUNITY_CACHE_TTL: int = 600               
    REDIS_FEED_CACHE_TTL: int = 120                    
    REDIS_TRENDING_TTL: int = 3600                    
    REDIS_SESSION_TTL: int = 7 * 24 * 3600             
    REDIS_ONLINE_TTL: int = 300                        
    REDIS_RATE_LIMIT_TTL: int = 60                    

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        extra="ignore",
    )


settings = Settings()
