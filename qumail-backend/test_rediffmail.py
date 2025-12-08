"""Test provider detection and connectivity for Rediffmail"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.provider_registry import detect_provider
from app.services.mail_connectivity import test_pop3_connection, test_smtp_connection

async def main():
    email = 'omkarsarswat@rediffmail.com'
    password = '9860545806@aA'
    
    print('='*60)
    print('1. PROVIDER DETECTION')
    print('='*60)
    result = detect_provider(email)
    print(f"Mode: {result['mode']}")
    print(f"Provider: {result['provider']}")
    if result['settings']:
        s = result['settings']
        print(f"POP3: {s['imap_host']}:{s['imap_port']} ({s['imap_security']})")
        print(f"SMTP: {s['smtp_host']}:{s['smtp_port']} ({s['smtp_security']})")
        print(f"Notes: {s['notes']}")
    
    print()
    print('='*60)
    print('2. POP3 CONNECTION TEST (Rediffmail uses POP3, not IMAP)')
    print('='*60)
    try:
        pop3_result = await test_pop3_connection(
            host='pop.rediffmail.com',
            port=995,
            security='ssl',
            username=email,
            password=password
        )
        print(f"Status: {pop3_result['status']}")
        print(f"Message: {pop3_result['message']}")
    except Exception as e:
        print(f'POP3 Error: {e}')
    
    print()
    print('='*60)
    print('3. SMTP CONNECTION TEST')
    print('='*60)
    try:
        smtp_result = await test_smtp_connection(
            host='smtp.rediffmail.com',
            port=465,
            security='ssl',
            username=email,
            password=password
        )
        print(f"Status: {smtp_result['status']}")
        print(f"Message: {smtp_result['message']}")
    except Exception as e:
        print(f'SMTP Error: {e}')

if __name__ == '__main__':
    asyncio.run(main())
