import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.gmail_service import GmailService
from app.services.complete_email_service import CompleteEmailService
from app.mongo_models import EmailDocument

@pytest.mark.asyncio
async def test_gmail_service_send_email_with_headers():
    """Test that GmailService adds custom headers to the MIME message"""
    service = GmailService()
    
    # Mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"id": "msg123", "threadId": "thread123"}
    
    # Mock context manager returned by post()
    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__.return_value = mock_response
    mock_post_ctx.__aexit__.return_value = None
    
    # Mock session
    mock_session = MagicMock()
    mock_session.post.return_value = mock_post_ctx
    
    # Mock ClientSession context manager
    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    
    with patch('aiohttp.ClientSession', return_value=mock_session_ctx):
        message = {
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'bodyText': 'Test Body',
            'headers': {
                'X-Custom-Header': 'CustomValue',
                'X-QuMail-Flow-ID': 'flow123'
            }
        }
        
        # We need to inspect the raw payload sent to Gmail API
        # The payload is base64 encoded MIME
        await service.send_email("fake_token", message)
        
        # Verify post was called
        assert mock_session.post.called
        call_args = mock_session.post.call_args
        url = call_args[0][0]
        kwargs = call_args[1]
        
        assert url.endswith("/messages/send")
        json_data = kwargs['json']
        raw_b64 = json_data['raw']
        
        # Decode base64 to check headers
        import base64
        from email import message_from_bytes
        
        raw_bytes = base64.urlsafe_b64decode(raw_b64)
        mime_msg = message_from_bytes(raw_bytes)
        
        assert mime_msg['X-Custom-Header'] == 'CustomValue'
        assert mime_msg['X-QuMail-Flow-ID'] == 'flow123'
        assert mime_msg['Subject'] == 'Test Subject'

@pytest.mark.asyncio
async def test_complete_email_service_injects_headers():
    """Test that CompleteEmailService injects headers when sending encrypted email"""
    service = CompleteEmailService()
    
    # Mock dependencies
    service.encryption_service = AsyncMock()
    service.encryption_service.encrypt_level_1_otp.return_value = {
        'encrypted_content': 'encrypted_data',
        'metadata': {'flow_id': 'flow123', 'key_id': 'key123', 'nonce': 'nonce123', 'auth_tag': 'tag123'},
        'algorithm': 'OTP-Quantum',
        'auth_tag': 'tag123'
    }
    
    # Mock DB and Repositories
    mock_db = AsyncMock()
    mock_email_repo = AsyncMock()
    mock_key_usage_repo = AsyncMock()
    
    with patch('app.services.complete_email_service.EmailRepository', return_value=mock_email_repo), \
         patch('app.services.complete_email_service.KeyUsageRepository', return_value=mock_key_usage_repo), \
         patch('app.services.gmail_oauth.oauth_service.get_valid_access_token', return_value='token123'), \
         patch('app.services.gmail_service.gmail_service.send_email', new_callable=AsyncMock) as mock_send_email:
             
        mock_send_email.return_value = {'messageId': 'msg123'}
        mock_email_repo.create.return_value.id = 'email_id_123'
        mock_email_repo.create.return_value.flow_id = 'flow123'
        mock_email_repo.create.return_value.timestamp = MagicMock()
        mock_email_repo.create.return_value.timestamp.isoformat.return_value = '2023-01-01T00:00:00'
        
        await service.send_encrypted_email(
            sender_email='sender@example.com',
            sender_user_id='user123',
            recipient_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body',
            security_level=1,
            db=mock_db,
            gmail_credentials={'token': 'abc'}
        )
        
        # Verify send_email was called with headers
        assert mock_send_email.called
        call_args = mock_send_email.call_args
        message_arg = call_args[0][1] # second arg is message
        
        assert 'headers' in message_arg
        headers = message_arg['headers']
        assert headers['X-QuMail-Flow-ID'] == 'flow123'
        assert headers['X-QuMail-Key-ID'] == 'key123'
        assert headers['X-QuMail-Algorithm'] == 'OTP-Quantum'
        assert headers['X-QuMail-Security-Level'] == '1'
        assert headers['X-QuMail-Auth-Tag'] == 'tag123'
        assert headers['X-QuMail-Nonce'] == 'nonce123'

@pytest.mark.asyncio
async def test_complete_email_service_parses_headers():
    """Test that CompleteEmailService parses headers when syncing"""
    service = CompleteEmailService()
    
    # Mock dependencies
    mock_db = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_email_repo = AsyncMock()
    
    mock_user_repo.find_by_email.return_value.id = 'user123'
    mock_email_repo.find_by_gmail_id.return_value = None # No existing email
    
    # Mock Gmail Service response
    gmail_message = {
        'id': 'msg123',
        'subject': '[QuMail Encrypted] Test',
        'snippet': 'Encrypted content...',
        'customHeaders': {
            'x-qumail-flow-id': 'flow_header_123',
            'x-qumail-key-id': 'key_header_123',
            'x-qumail-algorithm': 'Algo-Header',
            'x-qumail-security-level': '2',
            'x-qumail-auth-tag': 'tag_header',
            'x-qumail-nonce': 'nonce_header'
        }
    }
    
    with patch('app.services.complete_email_service.UserRepository', return_value=mock_user_repo), \
         patch('app.services.complete_email_service.EmailRepository', return_value=mock_email_repo), \
         patch('app.services.gmail_oauth.oauth_service.get_valid_access_token', return_value='token123'), \
         patch('app.services.gmail_service.gmail_service.fetch_emails', new_callable=AsyncMock) as mock_fetch:
             
        mock_fetch.return_value = {'emails': [gmail_message]}
        
        await service.sync_gmail_encrypted_emails(
            user_email='user@example.com',
            gmail_credentials={},
            db=mock_db
        )
        
        # Verify email was created with data from headers
        assert mock_email_repo.create.called
        call_args = mock_email_repo.create.call_args
        email_doc = call_args[0][0]
        
        assert email_doc.flow_id == 'flow_header_123'
        assert email_doc.encryption_key_id == 'key_header_123'
        assert email_doc.encryption_algorithm == 'Algo-Header'
        assert email_doc.security_level == 2
        assert email_doc.encryption_metadata['auth_tag'] == 'tag_header'
        assert email_doc.encryption_metadata['nonce'] == 'nonce_header'
