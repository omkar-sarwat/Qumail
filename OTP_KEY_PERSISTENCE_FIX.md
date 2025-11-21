# OTP Key Persistence Fix

## Problem
Keys generated during `enc_keys` were immediately removed from the KeyPool, causing "Key not found" errors when `dec_keys` tried to retrieve them seconds later for decryption.

## Root Cause
1. `KeyPool.get_key()` called `self.keys.pop()` which permanently removed keys
2. This happened during `enc_keys` when generating encryption keys
3. By the time `dec_keys` was called (even seconds later), the key was gone from the pool
4. Both KME1 and KME2 returned 404 "Key not found"

## Solution
**Modified key lifecycle to support OTP while allowing enc_keys → dec_keys flow:**

### 1. KeyPool Changes (`keys/key_pool.py`)
- Added `remove` parameter to `get_key()` method (default `False`)
- When `remove=False`: Copy key without removing (for `enc_keys`)
- When `remove=True`: Remove key permanently (for OTP consumption)

### 2. KeyStore Changes (`keys/key_store.py`)
- Updated `get_new_key()` to pass through `remove` parameter
- Allows callers to control key removal behavior

### 3. External Router Changes (`router/external.py`)
- **enc_keys endpoint**: Calls `get_new_key(remove=False)` - keys stay in pool
- **dec_keys endpoint**: Now removes keys after successful retrieval:
  - Calls `remove_keys()` to delete from KeyStore
  - Removes from SharedKeyPool if present
  - Enforces true OTP (one-time use)

## Key Lifecycle Now

```
1. enc_keys: Generate key → Copy to KeyStore (key stays in pool)
2. dec_keys: Retrieve key → Remove from KeyStore + pool (OTP consumed)
3. 2nd dec_keys: Key not found ✅ (correct OTP behavior)
```

## Testing
Run `test_otp_key_persistence.py` to verify:
1. Keys persist from enc_keys to dec_keys ✅
2. Keys are consumed after first dec_keys ✅
3. Second dec_keys fails (OTP enforced) ✅

## Deployment
Changes pushed to main branch. Render will automatically deploy KME servers with the fix.

## Impact
- ✅ Fixes "Key not found" errors during decryption
- ✅ Maintains true OTP security (keys consumed after use)
- ✅ No breaking changes to existing API
- ✅ Works for both cloud (Render) and local deployments
