-- Check most recent emails with encryption metadata
SELECT 
    id,
    gmail_message_id,
    flow_id,
    subject,
    security_level,
    sender_email,
    receiver_email,
    LENGTH(body_encrypted) as encrypted_length,
    encryption_metadata,
    timestamp
FROM emails
ORDER BY timestamp DESC
LIMIT 5;
