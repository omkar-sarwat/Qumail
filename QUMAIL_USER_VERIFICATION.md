# QuMail User Verification System

## Overview

QuMail now implements a user verification system that ensures encrypted emails can only be sent to registered QuMail users. Since non-QuMail users cannot decrypt quantum-encrypted emails, this feature prevents sending encrypted content that recipients cannot access.

## How It Works

### 1. User Storage in MongoDB

When users authenticate with Google OAuth, they are automatically stored in the MongoDB `users` collection:

```python
# From gmail_oauth.py - _create_or_update_user()
user_doc = UserDocument(
    email=email,
    display_name=display_name,
    oauth_access_token=encrypted_access_token,
    oauth_refresh_token=encrypted_refresh_token,
    oauth_token_expiry=expires_at,
    last_login=datetime.utcnow()
)
user = await user_repo.create(user_doc)
```

### 2. Pre-Send Validation (Frontend)

Before sending an encrypted email, the frontend checks if all recipients are registered QuMail users:

```typescript
// From composerStore.ts
if (draft.securityLevel >= 1) {
  const checkResult = await apiService.checkQuMailUsers(allRecipients)
  const nonQuMailUsers = allRecipients.filter(
    email => !checkResult.results[email]?.is_qumail_user
  )
  
  if (nonQuMailUsers.length > 0) {
    toast.error(`Cannot send encrypted email. Recipients not registered: ${userList}`)
    return false
  }
}
```

### 3. Backend Verification (Double-Check)

The backend also verifies recipients in `complete_email_service.py`:

```python
# Verify recipient is a registered QuMail user
user_repo = UserRepository(db)
recipient_user = await user_repo.find_by_email(recipient_email)

if not recipient_user:
    return {
        'success': False,
        'error': 'recipient_not_qumail_user',
        'message': f"Cannot send encrypted email to {recipient_email}..."
    }
```

## API Endpoints

### Check QuMail Users

**Endpoint:** `POST /api/v1/users/check`

**Purpose:** Validate if email addresses belong to registered QuMail users.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@example.com"]
}
```

**Response:**
```json
{
  "results": {
    "user1@example.com": {
      "is_qumail_user": true,
      "display_name": "User One"
    },
    "user2@example.com": {
      "is_qumail_user": false
    }
  }
}
```

## Error Handling

### Frontend Error Messages

When a recipient is not a QuMail user:
- **Pre-send check:** "Cannot send encrypted email. The following recipients are not registered QuMail users: [emails]. They need to sign up for QuMail first."
- **Server rejection:** "Cannot send encrypted email: [email] is not a registered QuMail user. They need to sign up for QuMail first to receive quantum-encrypted emails."

### Backend Error Response

```json
{
  "error": "recipient_not_qumail_user",
  "message": "Cannot send encrypted email to user@example.com. Recipient is not a registered QuMail user and cannot decrypt quantum-encrypted emails.",
  "recipient_email": "user@example.com"
}
```

## Files Modified

### Backend

1. **`qumail-backend/app/services/complete_email_service.py`**
   - Added QuMail user verification before encryption
   - Returns structured error when recipient is not a QuMail user

2. **`qumail-backend/app/routes/emails.py`**
   - Updated `send_quantum_email()` to handle "recipient_not_qumail_user" error
   - Returns HTTP 400 with detailed error message

3. **`qumail-backend/app/services/quantum_encryption.py`**
   - Added error handling for non-QuMail user recipients
   - Raises `ValueError` with descriptive message

4. **`qumail-backend/app/main.py`**
   - Added `/api/v1/users/check` endpoint for bulk user verification
   - Added `UserRepository` import

### Frontend

1. **`qumail-frontend/src/services/api.ts`**
   - Added `checkQuMailUsers()` method for pre-send validation

2. **`qumail-frontend/src/stores/composerStore.ts`**
   - Added pre-send validation for encrypted emails
   - Improved error handling for structured error responses

## User Registration Flow

1. User visits QuMail application
2. Clicks "Sign in with Google"
3. Completes Google OAuth flow
4. Backend creates/updates user in MongoDB
5. User is now a "registered QuMail user"
6. Can receive encrypted emails from other QuMail users

## Security Benefits

1. **Prevents Wasted Encryption:** Avoids encrypting emails that recipients cannot decrypt
2. **Clear User Experience:** Users know immediately if recipient can't receive encrypted email
3. **Double Validation:** Both frontend and backend verify recipients
4. **Graceful Degradation:** If frontend check fails, backend still validates

## Testing

### Test User Check API

```bash
curl -X POST http://localhost:8000/api/v1/users/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"emails": ["test@example.com"]}'
```

### Test Send to Non-QuMail User

1. Login to QuMail
2. Compose new email with security level 1-4
3. Enter recipient email that is NOT registered in QuMail
4. Click Send
5. Should see error: "Cannot send encrypted email..."

## Future Enhancements

1. **Invite System:** Allow sending invitation emails to non-QuMail users
2. **Fallback Encryption:** Option to send with standard encryption to non-QuMail users
3. **User Directory:** Search registered QuMail users when composing
4. **Contact Sync:** Highlight which contacts are QuMail users
