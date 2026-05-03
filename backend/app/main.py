from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from .database import engine
from . import models  # must import models

# =========================
# 🚦 RATE LIMITER SETUP
# =========================
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"]  # per IP
)

app = FastAPI(title="Wishbridge API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# =========================
# 🛡️ SECURITY MIDDLEWARE
# =========================
from app.middleware.security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)


# =========================
# 📁 STATIC FILES
# =========================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =========================
# 🧱 DB INIT
# =========================
def create_tables():
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


@app.on_event("startup")
def on_startup():
    create_tables()


# =========================
# 🌐 CORS (SECURED)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://yourfrontend.vercel.app"  # CHANGE THIS IN PROD
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# 📦 ROUTES
# =========================
from .routes import (
    wishes,
    users,
    grants,
    reports,
    thanks,
    admin
)

app.include_router(wishes.router, prefix="/wishes", tags=["wishes"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(grants.router, prefix="/grants", tags=["grants"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(thanks.router, prefix="/thanks", tags=["thanks"])

# 🔥 ADMIN ROUTER
app.include_router(admin.router, tags=["admin"])


# =========================
# 💳 PAYMENT + WALLET ROUTES
# =========================
from .routes import payments
app.include_router(payments.router)

from .routes import wallet
app.include_router(wallet.router)


# =========================
# 🏠 ROOT
# =========================
@app.get("/")
def root():
    return {"message": "Wishbridge API is running"}