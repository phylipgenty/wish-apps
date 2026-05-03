from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func
from ..database import Base


class Grant(Base):
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)
    wish_id = Column(Integer, ForeignKey("wishes.id"))
    granter_id = Column(Integer, ForeignKey("users.id"))

    timestamp = Column(DateTime, server_default=func.now())

    # status flow:
    # pending_payment → completed → failed (optional future states)
    status = Column(String, default="pending")

    proof_submitted = Column(String, nullable=True)

    # 💳 NEW: Paystack / payment reference tracking
    reference = Column(String, nullable=True)