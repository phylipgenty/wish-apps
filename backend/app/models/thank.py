from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from ..database import Base

class Thank(Base):
    __tablename__ = "thanks"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("wishes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, server_default=func.now())