import asyncio
from app.services.gmail_service import gmail_service
from app.services.gmail_oauth import oauth_service
from app.database import SessionLocal

async def main():
    async with SessionLocal() as session:
        token = await oauth_service.get_valid_access_token('sarswatomkar8625@gmail.com', session)
    message = {
        'from': 'sarswatomkar8625@gmail.com',
        'to': 'sarswatomkar009@gmail.com',
        'subject': 'Plain test',
        'bodyText': 'This is a plain text test',
    }
    result = await gmail_service.send_email(token, message)
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
