from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, func
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"

    # =========================
    # 🔑 CORE IDENTITY
    # =========================
    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # =========================
    # 📊 USER STATS
    # =========================
    karma_score = Column(Integer, default=0)
    streak_count = Column(Integer, default=0)
    total_grants = Column(Integer, default=0)
    successful_receipts = Column(Integer, default=0)

    # =========================
    # 🔐 STATUS FLAGS
    # =========================
    is_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # =========================
    # 🧑 PROFILE DATA
    # =========================
    avatar_url = Column(String, nullable=True)

    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)

    # =========================
    # 📧 EMAIL SYSTEM
    # =========================
    verification_token = Column(String, nullable=True)

    # =========================
    # 🔁 PASSWORD RESET SYSTEM (NEW)
    # =========================
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # =========================
    # ⏱ TIMESTAMPS
    # =========================
    created_at = Column(DateTime, server_default=func.now())

    # =========================
    # 🔗 RELATIONSHIPS
    # =========================
    wishes = relationship("Wish", back_populates="user")