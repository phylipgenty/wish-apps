from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import secrets
import hmac
import hashlib

from ..database import get_db
from ..models.user import User
from ..models.wallet import Wallet
from ..models.transaction import Transaction
from ..models.grant import Grant
from ..models.wish import Wish
from ..models.notification import Notification
from ..services.vtu_service import VTUService
from ..config import settings
from .users import get_current_user


router = APIRouter(prefix="/payments", tags=["payments"])

vtu = VTUService()

USD_TO_NGN = 1500


# =========================
# 📦 REQUEST SCHEMA
# =========================
class InitPaymentRequest(BaseModel):
    amount: float


# =========================
# 💰 INIT PAYMENT (TOPUP)
# =========================
@router.post("/initialize")
async def initialize_payment(
    req: InitPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    amount = req.amount

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    ref = f"WISH-{current_user.id}-{secrets.token_hex(8)}"

    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        type="deposit",
        reference=ref,
        status="pending"
    )
    db.add(tx)
    db.commit()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.paystack.co/transaction/initialize",
            headers={
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            },
            json={
                "email": current_user.email,
                "amount": int(amount * 100),
                "reference": ref,
                "callback_url": settings.PAYSTACK_CALLBACK_URL
            }
        )

    data = resp.json()

    if not data.get("status"):
        raise HTTPException(status_code=500, detail="Paystack initialization failed")

    return {
        "authorization_url": data["data"]["authorization_url"],
        "reference": ref
    }


# =========================
# 🔐 WEBHOOK
# =========================
@router.post("/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    signature = request.headers.get("x-paystack-signature")

    body = await request.body()
    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if signature != computed_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = payload.get("event")

    if event == "charge.success":
        data = payload["data"]
        ref = data["reference"]

        # -------------------------
        # WALLET TOPUP
        # -------------------------
        tx = db.query(Transaction).filter(Transaction.reference == ref).first()

        if tx and tx.status != "success":
            tx.status = "success"

            wallet = db.query(Wallet).filter(Wallet.user_id == tx.user_id).first()
            if not wallet:
                wallet = Wallet(user_id=tx.user_id, balance=0.0)
                db.add(wallet)
                db.flush()

            wallet.balance += tx.amount
            db.commit()

            return {"status": "wallet_topup_success"}

        # -------------------------
        # GRANT FLOW
        # -------------------------
        grant = db.query(Grant).filter(
            Grant.reference == ref,
            Grant.status == "pending_payment"
        ).first()

        if not grant:
            return {"status": "ignored"}

        wish = db.query(Wish).filter(Wish.id == grant.wish_id).first()

        if not wish:
            grant.status = "failed"
            db.commit()
            return {"status": "failed"}

        required_ngn = wish.estimated_cost * USD_TO_NGN

        try:
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
        except Exception as e:
            grant.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"VTU error: {str(e)}")

        if result.get("status") != "success":
            grant.status = "failed"
            db.commit()
            return {"status": "vtu_failed"}

        grant.status = "completed"
        wish.status = "granted"

        user = db.query(User).filter(User.id == grant.granter_id).first()
        if user:
            user.karma_score += 10
            user.total_grants += 1

        # =========================
        # 🔔 NOTIFICATION (ADDED)
        # =========================
        notification = Notification(
            user_id=wish.user_id,
            message=f"🎉 Your wish '{wish.title}' was granted!",
            is_read=False
        )
        db.add(notification)

        tx = Transaction(
            user_id=grant.granter_id,
            amount=required_ngn,
            type="grant",
            reference=ref,
            status="success"
        )
        db.add(tx)

        db.commit()

        return {"status": "grant_completed"}

    return {"status": "ignored"}


# =========================
# 🔍 VERIFY TOPUP
# =========================
@router.get("/verify")
async def verify_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        )

    data = resp.json()

    if not data.get("status"):
        raise HTTPException(status_code=400, detail="Verification failed")

    payment = data["data"]

    if payment.get("status") != "success":
        return {"status": "failed"}

    amount = payment["amount"] / 100

    tx = db.query(Transaction).filter(Transaction.reference == reference).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == "success":
        return {"status": "already_verified"}

    tx.status = "success"

    wallet = db.query(Wallet).filter(Wallet.user_id == tx.user_id).first()
    if not wallet:
        wallet = Wallet(user_id=tx.user_id, balance=0.0)
        db.add(wallet)
        db.flush()

    wallet.balance += amount

    db.commit()

    return {"status": "success"}


# =========================
# 🎯 VERIFY GRANT
# =========================
@router.get("/verify-grant")
async def verify_grant(
    grant_id: int,
    reference: str,
    db: Session = Depends(get_db)
):

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        )

    data = resp.json()

    if not data.get("status") or data["data"]["status"] != "success":
        return {"status": "failed", "message": "Payment not successful"}

    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.status == "pending_payment"
    ).first()

    if not grant:
        return {"status": "failed", "message": "Grant not found"}

    wish = db.query(Wish).filter(Wish.id == grant.wish_id).first()

    if not wish:
        return {"status": "failed", "message": "Wish not found"}

    required_ngn = wish.estimated_cost * USD_TO_NGN

    try:
        if wish.wish_type == "airtime":
            result = await vtu.buy_airtime(
                wish.phone_number,
                required_ngn,
                wish.network
            )
        else:
            result = await vtu.buy_data(
                wish.phone_number,
                wish.data_plan_id,
                wish.network
            )

        if result.get("status") != "success":
            return {"status": "failed", "message": "VTU failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    wish.status = "granted"
    grant.status = "completed"

    granter = db.query(User).filter(User.id == grant.granter_id).first()
    if granter:
        granter.karma_score += 10
        granter.total_grants += 1

    # =========================
    # 🔔 NOTIFICATION (ADDED)
    # =========================
    notification = Notification(
        user_id=wish.user_id,
        message=f"🎉 Your wish '{wish.title}' was granted!",
        is_read=False
    )
    db.add(notification)

    db.commit()

    return {"status": "success"}