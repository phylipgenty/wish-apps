from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # =========================
    # 🗄️ DATABASE
    # =========================
    DATABASE_URL: str = "sqlite:///./wishbridge.db"

    # =========================
    # 🔐 AUTH
    # =========================
    SECRET_KEY: str   # no default – must be in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # =========================
    # 📧 EMAIL (SMTP)
    # =========================
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    # =========================
    # 💳 PAYSTACK
    # =========================
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    PAYSTACK_CALLBACK_URL: str = "http://127.0.0.1:3000/wallet/topup-success.html"

    # =========================
    # 📡 INLOMAX VTU
    # =========================
    INLOMAX_API_KEY: str
    INLOMAX_BASE_URL: str = "https://inlomax.com"
    INLOMAX_TIMEOUT: int = 30

    class Config:
        env_file = ".env"

settings = Settings()