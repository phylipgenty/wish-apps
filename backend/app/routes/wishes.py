import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..database import get_db
from ..models.wish import Wish
from ..models.user import User
from ..models.thank import Thank

from ..schemas.wish_schema import WishCreate, WishOut
from .users import get_current_user


router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# =========================
# 📝 CREATE WISH (USER)
# =========================
@router.post("/")
def create_wish(
    wish: WishCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 🚪 EMAIL VERIFICATION CHECK (NEW)
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before posting."
        )

    # 💰 COST LIMIT CHECK
    MAX_COST_USD = 10.0
    if wish.estimated_cost > MAX_COST_USD:
        raise HTTPException(
            status_code=400,
            detail=f"Estimated cost cannot exceed ${MAX_COST_USD} USD"
        )

    # 🧠 KARMA CHECK
    if current_user.karma_score < 10:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient karma. You need 10 karma to post a wish. Current karma: {current_user.karma_score}"
        )

    if current_user.karma_score < wish.karma_required:
        raise HTTPException(
            status_code=403,
            detail=f"This wish requires {wish.karma_required} karma. Your karma: {current_user.karma_score}"
        )

    new_wish = Wish(
        **wish.dict(exclude_unset=True),
        user_id=current_user.id,
        status="active",
        report_count=0
    )

    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)

    return new_wish


# =========================
# 🛡️ ADMIN CREATE WISH
# =========================
@router.post("/admin/create")
def admin_create_wish(
    wish: WishCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    MAX_COST_USD = 10.0
    if wish.estimated_cost > MAX_COST_USD:
        raise HTTPException(
            status_code=400,
            detail=f"Estimated cost cannot exceed ${MAX_COST_USD} USD"
        )

    new_wish = Wish(
        **wish.dict(exclude_unset=True),
        user_id=current_user.id,
        status="active",
        report_count=0
    )

    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)

    return new_wish


# =========================
# 📤 UPLOAD PROOF
# =========================
@router.post("/upload-proof")
async def upload_proof(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images allowed")

    timestamp = int(datetime.utcnow().timestamp())
    filename = f"{current_user.id}_{timestamp}_{file.filename.replace(' ', '_')}"
    path = UPLOAD_DIR / filename

    with path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"proof_url": f"/uploads/{filename}"}


# =========================
# 🎲 RANDOM WISH
# =========================
@router.get("/random")   # ❌ removed response_model
def get_random_wish(db: Session = Depends(get_db)):

    # 🔗 Join with User to get username
    wish = (
        db.query(Wish)
        .outerjoin(User, User.id == Wish.user_id)
        .filter(Wish.status == "active")
        .order_by(func.random())
        .first()
    )

    if not wish:
        # 🧪 fallback dummy wish
        return {
            "id": 0,
            "title": "Example: Buy me a coffee",
            "description": "I need a small coffee to get through my shift.",
            "estimated_cost": 5.0,
            "category_tag": "Food",
            "wish_type": "Digital",
            "user_id": None,
            "username": None,
            "is_anonymous": True,
            "proof_url": None,
            "status": "active",
            "created_at": datetime.utcnow(),
            "expires_at": None,
            "report_count": 0,
            "occasion": None,
            "karma_required": 0,
            "geo_location": None,
            "latitude": None,
            "longitude": None,
        }

    # 👤 Respect anonymity
    username = (
        wish.user.username
        if wish.user and not wish.is_anonymous
        else None
    )

    return {
        "id": wish.id,
        "title": wish.title,
        "description": wish.description,
        "estimated_cost": wish.estimated_cost,
        "category_tag": wish.category_tag,
        "wish_type": wish.wish_type,
        "user_id": wish.user_id,
        "username": username,
        "is_anonymous": wish.is_anonymous,
        "proof_url": wish.proof_url,
        "status": wish.status,
        "created_at": wish.created_at,
        "expires_at": wish.expires_at,
        "report_count": wish.report_count,
        "occasion": wish.occasion,
        "karma_required": wish.karma_required,
        "geo_location": wish.geo_location,
        "latitude": wish.latitude,
        "longitude": wish.longitude,
    }
# =========================
# 📦 GET WISH BY ID (WITH USER INFO)
# =========================
@router.get("/{wish_id}")
def get_wish(wish_id: int, db: Session = Depends(get_db)):

    wish = (
        db.query(Wish)
        .outerjoin(User, User.id == Wish.user_id)
        .filter(Wish.id == wish_id)
        .first()
    )

    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")

    # 👤 Respect anonymity
    username = (
        wish.user.username
        if wish.user and not wish.is_anonymous
        else None
    )

    return {
        "id": wish.id,
        "title": wish.title,
        "description": wish.description,
        "estimated_cost": wish.estimated_cost,
        "category_tag": wish.category_tag,
        "wish_type": wish.wish_type,
        "user_id": wish.user_id,
        "username": username,
        "is_anonymous": wish.is_anonymous,
        "proof_url": wish.proof_url,
        "status": wish.status,
        "occasion": wish.occasion,
        "karma_required": wish.karma_required,
        "geo_location": wish.geo_location,
        "latitude": wish.latitude,
        "longitude": wish.longitude,
        "created_at": wish.created_at,
        "expires_at": wish.expires_at,
        "report_count": wish.report_count
    }
# =========================
# 🔥 SUCCESS STORIES
# =========================
@router.get("/stories/latest")
def get_success_stories(limit: int = 20, db: Session = Depends(get_db)):

    results = (
        db.query(
            Wish,
            func.count(Thank.id).label("heart_count")
        )
        .outerjoin(Thank, Thank.story_id == Wish.id)
        .filter(
            Wish.status == "granted",
            Wish.proof_url.isnot(None)
        )
        .group_by(Wish.id)
        .order_by(Wish.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": wish.id,
            "title": wish.title,
            "description": wish.description,
            "estimated_cost": wish.estimated_cost,
            "category_tag": wish.category_tag,
            "proof_url": wish.proof_url,
            "heart_count": heart_count or 0
        }
        for wish, heart_count in results
    ]


# =========================
# 🗺️ KINDNESS MAP
# =========================
@router.get("/map/kindness")
def get_kindness_map_points(db: Session = Depends(get_db)):

    points = db.query(Wish).filter(
        Wish.status == "granted",
        Wish.proof_url.isnot(None),
        Wish.latitude.isnot(None),
        Wish.longitude.isnot(None)
    ).order_by(Wish.created_at.desc()).limit(100).all()

    return [
        {
            "id": w.id,
            "title": w.title,
            "description": w.description,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "proof_url": w.proof_url,
        }
        for w in points
    ]