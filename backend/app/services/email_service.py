from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from ..config import settings

async def send_email(recipient: str, subject: str, html: str):
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=html,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)