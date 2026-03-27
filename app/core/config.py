import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Glucks Trader Backend"
APP_VERSION = "1.0.0"
API_V1_PREFIX = "/api"

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

FRONTEND_ORIGINS_RAW = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
)

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in FRONTEND_ORIGINS_RAW.split(",")
    if origin.strip()
]

SECRET_KEY = os.getenv("SECRET_KEY", "glucks_super_secret_key_change_this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./glucks.db")

PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "")
PAGBANK_ENV = os.getenv("PAGBANK_ENV", "sandbox")

PAGBANK_NOTIFICATION_URL = os.getenv(
    "PAGBANK_NOTIFICATION_URL",
    "http://127.0.0.1:8000/api/payments/pagbank/webhook"
)

FRONTEND_SUCCESS_URL = os.getenv(
    "FRONTEND_SUCCESS_URL",
    "http://localhost:5173/premium"
)