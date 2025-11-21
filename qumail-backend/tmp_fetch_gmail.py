import asyncio
import json
import sqlite3
import os
import aiohttp

from app.services.gmail_service import gmail_service
from app.services.gmail_oauth import oauth_service
from app.database import SessionLocal

async def main():
    # Locate user email with token
    conn = sqlite3.connect('qumail.db')
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE oauth_access_token IS NOT NULL LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        print('No user with OAuth token found')
        return
    user_email = row[0]
    async with SessionLocal() as session:
        token = await oauth_service.get_valid_access_token(user_email, session)
    print('Using access token for', user_email)
    folder = 'inbox'
    data = await gmail_service.fetch_emails(token, folder=folder, max_results=5)
    for msg in data['emails']:
        print(json.dumps({'folder': folder, 'id': msg.get('id'), 'subject': msg.get('subject'), 'snippet': msg.get('snippet')[:120]}, indent=2))

    # Fetch sent items for verification
    sent = await gmail_service.fetch_emails(token, folder='sent', max_results=5)
    for msg in sent['emails']:
        print(json.dumps({'folder': 'sent', 'id': msg.get('id'), 'subject': msg.get('subject'), 'snippet': msg.get('snippet')[:120]}, indent=2))

    # Inspect most recent sent message in detail (if available)
    if sent['emails']:
        latest_sent_id = sent['emails'][0]['id']
        detail = await gmail_service.get_email_by_id(token, latest_sent_id)
        print(json.dumps({
            'detail_for': latest_sent_id,
            'subject': detail.get('subject'),
            'bodyText': detail.get('bodyText', '')[:500],
            'labels': detail.get('labels'),
            'attachments': detail.get('attachments', []),
            'bodyHtml': detail.get('bodyHtml', '')[:200]
        }, indent=2))
    if len(sent['emails']) > 1:
        bounce_id = sent['emails'][1]['id']
        # Fetch raw data for bounce to inspect nested payload
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{bounce_id[6:] if bounce_id.startswith('gmail_') else bounce_id}?format=raw"
            async with session.get(url, headers=headers) as resp:
                raw_data = await resp.json()
        raw_payload = raw_data.get('raw', '')
        if raw_payload:
            import base64
            decoded_raw = base64.urlsafe_b64decode(raw_payload + '===').decode(errors='ignore')
        else:
            decoded_raw = ''
        bounce_detail = await gmail_service.get_email_by_id(token, bounce_id)
        print(json.dumps({
            'detail_for': bounce_id,
            'subject': bounce_detail.get('subject'),
            'bodyText': bounce_detail.get('bodyText', '')[:500],
            'labels': bounce_detail.get('labels'),
            'attachments': bounce_detail.get('attachments', []),
            'bodyHtml': bounce_detail.get('bodyHtml', '')[:200],
            'rawSnippet': raw_data.get('snippet', ''),
            'rawHeader': decoded_raw[:500]
        }, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
