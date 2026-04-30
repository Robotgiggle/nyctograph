from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_DOMAIN: str               # domain that the app will run at (ie http://localhost:8000), used to generate links in emails
    DATABASE_URL: str             # connection URL for the PostgreSQL database
    RESEND_API_KEY: str           # API key for Resend, the email provider
    STRIPE_API_KEY: str           # API key for Stripe, the payment provider
    STRIPE_WEBHOOK_SECRET: str    # secret key for the Stripe webhook that triggers purchase fulfillment
    COOKIE_SECRET_KEY: str        # secret key used to encrypt browser cookies
    ADMIN_ACCOUNT_PW: str         # password to be used for the admin accounts when initially building the database
    GLOBAL_CALC_INTERVAL: int = 2 # interval in minutes between attempts to recalculate global stats
    ROW_PRICE_CENTS: int = 1      # price in cents per row of data requested as a researcher

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() # type: ignore