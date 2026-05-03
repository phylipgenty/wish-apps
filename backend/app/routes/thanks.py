from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.wish import Wish
from ..models.thank import Thank
from ..models.user import User
from ..models.notification import Notification
from .users import get_current_user

router = APIRouter()

@router.post("/{story_id}")
def thank_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if story exists and is granted
    story = db.query(Wish).filter(Wish.id == story_id, Wish.status == "granted").first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Ensure user hasn't already thanked this story
    existing = db.query(Thank).filter(
        Thank.story_id == story_id,
        Thank.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already thanked this story")
    
    # Add the thank record
    thank = Thank(story_id=story_id, user_id=current_user.id)
    db.add(thank)
    
    # Give +2 karma to the wisher (owner of the granted wish)
    wisher = db.query(User).filter(User.id == story.user_id).first()
    if wisher:
        wisher.karma_score += 2
        # Create a notification for the wisher
        notif = Notification(
            user_id=wisher.id,
            message=f"❤️ {current_user.username} thanked you for your wish: {story.title}"
        )
        db.add(notif)
    
    db.commit()
    
    # Return updated thank count
    count = db.query(Thank).filter(Thank.story_id == story_id).count()
    return {"thank_count": count}