import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

async def test():
    conf = ConnectionConfig(
        MAIL_USERNAME="team.wishapp@gmail.com",
        MAIL_PASSWORD="yqicpebgpzpapive",
        MAIL_FROM="team.wishapp@gmail.com",
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    message = MessageSchema(
        subject="Test",
        recipients=["phylipgenty@gmail.com"],  # replace with your email
        body="<h1>Test</h1>",
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    print("Email sent successfully!")

asyncio.run(test())