from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WishBase(BaseModel):
    title: str
    description: str
    occasion: Optional[str] = None
    estimated_cost: float
    is_anonymous: bool = False
    category_tag: str
    proof_url: Optional[str] = None
    karma_required: int = 0

    # 🌍 LOCATION FIELDS
    geo_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # 📌 TYPE OF WISH
    wish_type: str  # Physical, Digital, Story, airtime, data

# =========================
# 🆕 CREATE SCHEMA
# =========================
class WishCreate(WishBase):

    # 📱 VTU FIELDS
    phone_number: Optional[str] = None
    network: Optional[str] = None
    data_plan_id: Optional[str] = None   # Inlomax numeric Service ID (as string)

# =========================
# 📤 OUTPUT SCHEMA
# =========================
class WishOut(WishBase):

    id: int
    user_id: int
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    report_count: int

    # 📱 VTU FIELDS (returned to frontend too)
    phone_number: Optional[str] = None
    network: Optional[str] = None
    data_plan_id: Optional[str] = None

    class Config:
        orm_mode = True