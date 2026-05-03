from sqlalchemy import Column, Integer, Float, String, DateTime, func, ForeignKey
from ..database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String)          # "deposit", "grant"
    reference = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, success, failed
    created_at = Column(DateTime, server_default=func.now())