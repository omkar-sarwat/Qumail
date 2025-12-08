"""Test provider detection for multiple providers"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.provider_registry import detect_provider, list_providers

def main():
    print('='*70)
    print('PROVIDER DETECTION TEST')
    print('='*70)
    
    test_emails = [
        'user@gmail.com',
        'user@yahoo.com',
        'user@outlook.com',
        'user@rediffmail.com',
        'user@zoho.com',
        'user@icloud.com',
        'user@aol.com',
        'user@gmx.com',
        'user@protonmail.com',
        'user@customdomain.org',  # Should be manual
    ]
    
    for email in test_emails:
        result = detect_provider(email)
        mode = result['mode']
        provider = result['provider']
        if result['settings']:
            s = result['settings']
            incoming = f"{s['imap_host']}:{s['imap_port']}"
            outgoing = f"{s['smtp_host']}:{s['smtp_port']}"
            print(f"  {email:35} -> {provider:20} | IN: {incoming:30} | OUT: {outgoing}")
        else:
            print(f"  {email:35} -> {provider:20} | Manual configuration required")
    
    print()
    print('='*70)
    print('ALL PRESET PROVIDERS')
    print('='*70)
    providers = list_providers()
    for p in providers:
        print(f"  {p['name']:20} | Domains: {', '.join(p['domains'])}")
        print(f"    SMTP: {p['smtp_host']}:{p['smtp_port']} ({p['smtp_security']})")
        print(f"    IMAP/POP3: {p['imap_host']}:{p['imap_port']} ({p['imap_security']})")
        if p['notes']:
            print(f"    Notes: {p['notes']}")
        print()

if __name__ == '__main__':
    main()
