import asyncio
from app.database import SessionLocal
from app.services.gmail_oauth import oauth_service
from app.services.real_encrypted_gmail import real_encrypted_gmail_service

async def main():
    sender_email = 'sarswatomkar8625@gmail.com'
    recipient_email = 'sarswatomkar009@gmail.com'
    user_id = 'ae4c21c8-8eec-4747-b18d-61679e15b573'

    async with SessionLocal() as session:
        token = await oauth_service.get_valid_access_token(sender_email, session)
        result = await real_encrypted_gmail_service.send_encrypted_email(
            sender_email=sender_email,
            recipient_email=recipient_email,
            subject='Test Quantum Direct',
            body='Hello from script',
            security_level=1,
            access_token=token,
            user_id=user_id,
            db=session
        )
        print(result)

if __name__ == '__main__':
    asyncio.run(main())
