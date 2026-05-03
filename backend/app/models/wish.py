from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    func,
    ForeignKey
)
from sqlalchemy.orm import relationship

from ..database import Base


class Wish(Base):
    __tablename__ = "wishes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # =========================
    # 📝 CORE WISH DATA
    # =========================
    title = Column(String)
    description = Column(String)
    occasion = Column(String, nullable=True)
    estimated_cost = Column(Float)

    status = Column(String, default="active")  # active, granted, expired, hidden
    is_anonymous = Column(Boolean, default=False)

    category_tag = Column(String)
    proof_url = Column(String, nullable=True)

    karma_required = Column(Integer, default=0)

    geo_location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)

    report_count = Column(Integer, default=0)

    wish_type = Column(String)

    # =========================
    # 📱 VTU / AIRTIME FEATURES
    # =========================
    phone_number = Column(String, nullable=True)   # recipient phone number
    network = Column(String, nullable=True)        # MTN, GLO, Airtel, 9mobile
    data_plan_id = Column(String, nullable=True)   # VTU provider plan code

    # =========================
    # 🔗 RELATIONSHIP
    # =========================
    user = relationship("User", back_populates="wishes")