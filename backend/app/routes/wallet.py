from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.wallet import Wallet
from .users import get_current_user
from ..models.user import User

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        return {"balance": 0.0}
    return {"balance": wallet.balance}