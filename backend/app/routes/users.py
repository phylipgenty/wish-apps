from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File
)

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

import shutil
import secrets
from pathlib import Path
import asyncio

# Email imports (RESET PASSWORD ENABLED)
from ..services.email_service import send_email

from ..database import get_db
from ..models.user import User
from ..models.notification import Notification
from ..schemas.user_schema import (
    UserCreate,
    UserOut,
    Token,
    UserUpdate,
    PublicUserOut
)
from ..config import settings

from pydantic import BaseModel   # ✅ REQUIRED for forgot password model

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


# =========================
# 🔐 HELPERS
# =========================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


# =========================
# 🔐 PASSWORD STRENGTH VALIDATOR (NEW)
# =========================
def validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")

    if not any(c in "!@#$%^&*" for c in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character (!@#$%^&*)")

    return True


# =========================
# 👤 CURRENT USER
# =========================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user


# =========================
# 🆕 SIGNUP
# =========================
@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate, db: Session = Depends(get_db)):

    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # ✅ PASSWORD VALIDATION ADDED HERE
    validate_password_strength(user.password)

    hashed = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        karma_score=10,
        streak_count=0,
        total_grants=0,
        successful_receipts=0,
        is_verified=False,
        is_email_verified=True,
        is_admin=False,
        avatar_url=None,
        verification_token=None
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# =========================
# 🔑 LOGIN
# =========================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


# =========================
# 👤 ME
# =========================
@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# =========================
# 🌍 PUBLIC PROFILE
# =========================
@router.get("/public/{user_id}", response_model=PublicUserOut)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return PublicUserOut(
        id=user.id,
        username=user.username,
        karma_score=user.karma_score,
        total_grants=user.total_grants,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
        joined=user.created_at,
        bio=user.bio,
        location=user.location,
        gender=user.gender,
        date_of_birth=user.date_of_birth
    )


# =========================
# ✏️ UPDATE PROFILE
# =========================
@router.put("/me", response_model=UserOut)
def update_profile(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if update.username:
        existing = db.query(User).filter(
            User.username == update.username,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

        current_user.username = update.username

    if update.email:
        existing = db.query(User).filter(
            User.email == update.email,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        current_user.email = update.email
        current_user.is_email_verified = True
        current_user.verification_token = None

    if update.password:
        validate_password_strength(update.password)  # ✅ ALSO ENFORCED HERE
        current_user.hashed_password = get_password_hash(update.password)

    if update.avatar_url:
        current_user.avatar_url = update.avatar_url

    if update.bio:
        current_user.bio = update.bio

    if update.location:
        current_user.location = update.location

    if update.gender:
        current_user.gender = update.gender

    if update.date_of_birth:
        current_user.date_of_birth = update.date_of_birth

    db.commit()
    db.refresh(current_user)

    return current_user


# =========================
# 🧑‍🎨 AVATAR UPLOAD
# =========================
@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    timestamp = int(datetime.utcnow().timestamp())
    filename = f"avatar_{current_user.id}_{timestamp}_{file.filename.replace(' ', '_')}"

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.avatar_url = f"/uploads/{filename}"

    db.commit()
    db.refresh(current_user)

    return {"avatar_url": current_user.avatar_url}


# =========================
# 🔔 NOTIFICATIONS
# =========================
@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(30).all()


@router.put("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()

    if not notif:
        raise HTTPException(status_code=404)

    notif.is_read = True
    db.commit()

    return {"message": "Marked as read"}


# =========================================================
# 🔐 PASSWORD RESET SYSTEM
# =========================================================

class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):

    email = req.email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"message": "If that email exists, we've sent a reset link"}

    token = secrets.token_urlsafe(32)

    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)

    db.commit()

    reset_link = f"http://127.0.0.1:3000/reset-password.html?token={token}"

    print(f"RESET LINK: {reset_link}")

    try:
        html = f"""
        <h2>Reset Your Password</h2>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">Reset Password</a>
        """

        await send_email(user.email, "Reset your password", html)

    except Exception as e:
        print(f"Email error: {e}")

    return {"message": "If that email exists, we've sent a reset link"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token has expired")

    validate_password_strength(new_password)  # ✅ ADDED HERE TOO

    user.hashed_password = get_password_hash(new_password)

    user.reset_token = None
    user.reset_token_expires = None

    db.commit()

    return {"message": "Password reset successful. You can now log in."}