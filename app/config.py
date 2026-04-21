from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_DOMAIN: str
    DATABASE_URL: str
    RESEND_API_KEY: str
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    COOKIE_SECRET_KEY: str
    ADMIN_ACCOUNT_PW: str
    GLOBAL_CALC_INTERVAL: int = 2
    ROW_PRICE_CENTS: int = 1

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() # type: ignore