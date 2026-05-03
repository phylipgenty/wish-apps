from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.wish import Wish
from ..schemas.wish_schema import WishCreate
from .users import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


# =========================
# 🔐 ADMIN GUARD
# =========================
def is_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# =========================
# 📊 STATS
# =========================
@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(is_admin_user)):
    total_users = db.query(User).count()
    total_wishes = db.query(Wish).count()
    total_grants = db.query(Wish).filter(Wish.status == "granted").count()
    total_flagged = db.query(Wish).filter(Wish.report_count >= 1).count()

    return {
        "total_users": total_users,
        "total_wishes": total_wishes,
        "total_grants": total_grants,
        "total_flagged": total_flagged
    }


# =========================
# 🚩 FLAGGED WISHES
# =========================
@router.get("/wishes/flagged")
def get_flagged_wishes(db: Session = Depends(get_db), admin: User = Depends(is_admin_user)):
    wishes = db.query(Wish).filter(
        Wish.report_count >= 1
    ).order_by(Wish.report_count.desc()).all()

    return wishes


# =========================
# 🚫 HIDE WISH
# =========================
@router.put("/wishes/{wish_id}/hide")
def hide_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(is_admin_user)
):
    wish = db.query(Wish).filter(Wish.id == wish_id).first()

    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")

    wish.status = "hidden"
    db.commit()

    return {"message": "Wish hidden"}


# =========================
# ✨ ADMIN CREATE WISH (FIXED)
# =========================
@router.post("/wishes/create")
def admin_create_wish(
    wish: WishCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(is_admin_user)
):
    MAX_COST_USD = 10.0

    if wish.estimated_cost > MAX_COST_USD:
        raise HTTPException(
            status_code=400,
            detail=f"Estimated cost cannot exceed ${MAX_COST_USD} USD"
        )

    new_wish = Wish(
        **wish.dict(exclude_unset=True),
        user_id=admin.id,
        status="active",
        report_count=0
    )

    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)

    return new_wish


# =========================
# 📦 GET ALL WISHES
# =========================
@router.get("/wishes/all")
def get_all_wishes(db: Session = Depends(get_db), admin: User = Depends(is_admin_user)):
    return db.query(Wish).order_by(Wish.created_at.desc()).all()


# =========================
# 🗑 DELETE WISH
# =========================
@router.delete("/wishes/{wish_id}")
def delete_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(is_admin_user)
):
    wish = db.query(Wish).filter(Wish.id == wish_id).first()

    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")

    db.delete(wish)
    db.commit()

    return {"message": "Wish deleted"}