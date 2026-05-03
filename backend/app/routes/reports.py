from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.wish import Wish
from ..models.user import User
from .users import get_current_user

router = APIRouter()

@router.post("/")
def report_wish(
    wish_id: int = Body(...),
    reason: str = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wish).filter(Wish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    wish.report_count += 1
    
    if current_user.karma_score > 100:
        wish.report_count += 1
    
    if wish.report_count >= 5:
        wish.status = "hidden"
    
    db.commit()
    return {"message": "Wish reported", "report_count": wish.report_count}