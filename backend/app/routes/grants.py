from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import secrets

from ..database import get_db
from ..models.grant import Grant
from ..models.wish import Wish
from ..models.user import User
from ..models.wallet import Wallet
from ..models.transaction import Transaction
from ..models.notification import Notification
from .users import get_current_user
from ..services.vtu_service import VTUService
from ..config import settings


router = APIRouter()
vtu = VTUService()

USD_TO_NGN = 1500


# =========================
# 📦 REQUEST SCHEMA
# =========================
class GrantRequest(BaseModel):
    wish_id: int
    method: str   # "wallet" | "paystack" | "manual"
    note: str = ""


@router.post("/")
async def create_grant(
    grant_req: GrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wish).filter(Wish.id == grant_req.wish_id).first()

    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")

    if wish.status != "active":
        raise HTTPException(status_code=400, detail="Wish already processed")

    required_ngn = wish.estimated_cost * USD_TO_NGN

    # =====================================================
    # 🧠 VTU VALIDATION
    # =====================================================
    if wish.wish_type in ["airtime", "data"]:
        if not wish.phone_number or not wish.network:
            raise HTTPException(status_code=400, detail="Missing phone or network")

        if wish.wish_type == "data" and not wish.data_plan_id:
            raise HTTPException(status_code=400, detail="Missing data plan ID")

    # =====================================================
    # 💰 WALLET FLOW
    # =====================================================
    if grant_req.method == "wallet":

        if wish.wish_type not in ["airtime", "data"]:
            raise HTTPException(status_code=400, detail="Wallet method only for VTU wishes")

        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()

        if not wallet:
            wallet = Wallet(user_id=current_user.id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)

        if wallet.balance < required_ngn:
            raise HTTPException(status_code=402, detail=f"Insufficient balance. Need ₦{required_ngn:,.0f}")

        # VTU execution
        if wish.wish_type == "airtime":
            result = await vtu.buy_airtime(
                phone=wish.phone_number,
                amount=required_ngn,
                network=wish.network
            )
        else:
            result = await vtu.buy_data(
                phone=wish.phone_number,
                plan_id=wish.data_plan_id,
                network=wish.network
            )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail="VTU transaction failed")

        wallet.balance -= required_ngn

        tx = Transaction(
            user_id=current_user.id,
            amount=required_ngn,
            type="grant",
            reference=f"WALLET-{wish.id}-{current_user.id}-{secrets.token_hex(4)}",
            status="success"
        )
        db.add(tx)

        wish.status = "granted"

        grant = Grant(
            wish_id=wish.id,
            granter_id=current_user.id,
            status="completed"
        )
        db.add(grant)

        current_user.karma_score += 10
        current_user.total_grants += 1

        # =========================
        # 🔔 NOTIFICATION (ADDED)
        # =========================
        notification = Notification(
            user_id=wish.user_id,
            message=f"🎉 Your wish '{wish.title}' was granted by {current_user.username}!",
            is_read=False
        )
        db.add(notification)

        db.commit()

        return {
            "message": "Wish granted via wallet",
            "new_balance": wallet.balance
        }

    # =====================================================
    # 💳 PAYSTACK FLOW
    # =====================================================
    elif grant_req.method == "paystack":

        if wish.wish_type not in ["airtime", "data"]:
            raise HTTPException(status_code=400, detail="Paystack only for VTU wishes")

        pending_grant = Grant(
            wish_id=wish.id,
            granter_id=current_user.id,
            status="pending_payment"
        )
        db.add(pending_grant)
        db.commit()
        db.refresh(pending_grant)

        ref = f"WISH-{wish.id}-{current_user.id}-{pending_grant.id}-{secrets.token_hex(6)}"

        callback_url = f"http://127.0.0.1:3000/dashboard.html?grant_id={pending_grant.id}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
                },
                json={
                    "email": current_user.email,
                    "amount": int(required_ngn * 100),
                    "reference": ref,
                    "callback_url": callback_url
                }
            )

        data = resp.json()

        if not data.get("status"):
            db.delete(pending_grant)
            db.commit()
            raise HTTPException(status_code=500, detail="Paystack initialization failed")

        pending_grant.reference = ref
        db.commit()

        return {
            "authorization_url": data["data"]["authorization_url"],
            "grant_id": pending_grant.id,
            "reference": ref
        }

    # =====================================================
    # 🧾 MANUAL FLOW
    # =====================================================
    elif grant_req.method == "manual":

        wish.status = "granted"

        grant = Grant(
            wish_id=wish.id,
            granter_id=current_user.id,
            status="completed"
        )
        db.add(grant)

        current_user.karma_score += 10
        current_user.total_grants += 1

        # =========================
        # 🔔 NOTIFICATION (ADDED)
        # =========================
        notification = Notification(
            user_id=wish.user_id,
            message=f"🎉 Your wish '{wish.title}' was granted by {current_user.username}!",
            is_read=False
        )
        db.add(notification)

        db.commit()

        return {
            "message": "Wish granted manually",
            "grant_id": grant.id
        }

    # =====================================================
    # ❌ INVALID METHOD
    # =====================================================
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")