from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Event Manager"
    MONGO_URI: str = "mongodb://127.0.0.1:27017"
    RABBIT_URI: str = "amqp://guest:guest@127.0.0.1:5672/"
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
