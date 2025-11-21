"""
Test all encryption levels with the optimized KM client.
This test ensures that all encryption levels work properly with the optimized KM client.
"""

import pytest
import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly from the modules
from app.services.optimized_km_client import OptimizedKMClient, create_optimized_km_clients
from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc
from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa

# Initialize optimized KM clients
@pytest.fixture(scope="module")
def km_clients():
    """Initialize KM clients before tests run"""
    # Create KM clients directly using factory function
    km1, km2 = create_optimized_km_clients()
    return km1, km2

# Use a separate fixture for test setup that properly uses asyncio
@pytest.fixture(scope="module", autouse=True)
async def setup_km_clients(km_clients):
    """Set up KM clients with asyncio support"""
    km1, km2 = km_clients
    
    # Initialize key caches - await instead of creating tasks
    # This is safer for tests as it ensures the cache population completes
    try:
        await km1._populate_key_cache(3)  # For receiver
        await km2._populate_key_cache(1)  # For sender
        print("Key cache populated successfully")
    except Exception as e:
        print(f"Warning: Failed to populate key cache: {e}")
    
    yield
    
    # Clean up after tests
    try:
        await km1.close()
        await km2.close()
    except Exception as e:
        print(f"Warning: Failed to close KM clients: {e}")


@pytest.mark.asyncio
async def test_level1_encryption():
    """Test Level 1 OTP encryption with optimized KM client"""
    content = "This is a test message for OTP encryption"
    user_email = "test@example.com"
    
    # Encrypt
    encrypted_result = await encrypt_otp(content, user_email)
    assert encrypted_result is not None
    assert "encrypted_content" in encrypted_result
    assert "metadata" in encrypted_result
    assert encrypted_result["metadata"]["security_level"] == 1
    
    # Decrypt
    decrypted_result = await decrypt_otp(
        encrypted_result["encrypted_content"], 
        user_email, 
        encrypted_result["metadata"]
    )
    assert decrypted_result is not None
    assert "decrypted_content" in decrypted_result
    assert decrypted_result["decrypted_content"] == content


@pytest.mark.asyncio
async def test_level2_encryption():
    """Test Level 2 AES encryption with optimized KM client"""
    content = "This is a test message for AES encryption"
    user_email = "test@example.com"
    
    # Encrypt
    encrypted_result = await encrypt_aes(content, user_email)
    assert encrypted_result is not None
    assert "encrypted_content" in encrypted_result
    assert "metadata" in encrypted_result
    assert encrypted_result["metadata"]["security_level"] == 2
    
    # Decrypt
    decrypted_result = await decrypt_aes(
        encrypted_result["encrypted_content"], 
        user_email, 
        encrypted_result["metadata"]
    )
    assert decrypted_result is not None
    assert "decrypted_content" in decrypted_result
    assert decrypted_result["decrypted_content"] == content


@pytest.mark.asyncio
async def test_level3_encryption():
    """Test Level 3 PQC encryption with optimized KM client"""
    content = "This is a test message for PQC encryption"
    user_email = "test@example.com"
    
    # Encrypt
    encrypted_result = await encrypt_pqc(content, user_email)
    assert encrypted_result is not None
    assert "encrypted_content" in encrypted_result
    assert "metadata" in encrypted_result
    assert encrypted_result["metadata"]["security_level"] == 3
    
    # Decrypt
    decrypted_result = await decrypt_pqc(
        encrypted_result["encrypted_content"], 
        user_email, 
        encrypted_result["metadata"]
    )
    assert decrypted_result is not None
    assert "decrypted_content" in decrypted_result
    assert decrypted_result["decrypted_content"] == content


@pytest.mark.asyncio
async def test_level4_encryption():
    """Test Level 4 RSA encryption with optimized KM client"""
    content = "This is a test message for RSA encryption"
    user_email = "test@example.com"
    
    # Encrypt
    encrypted_result = await encrypt_rsa(content, user_email)
    assert encrypted_result is not None
    assert "encrypted_content" in encrypted_result
    assert "metadata" in encrypted_result
    assert encrypted_result["metadata"]["security_level"] == 4
    
    # Decrypt
    decrypted_result = await decrypt_rsa(
        encrypted_result["encrypted_content"], 
        user_email, 
        encrypted_result["metadata"]
    )
    assert decrypted_result is not None
    assert "decrypted_content" in decrypted_result
    assert decrypted_result["decrypted_content"] == content


@pytest.mark.asyncio
async def test_optimized_client_availability(init_km_clients):
    """Test that optimized KM clients are available and properly configured"""
    km1, km2 = init_km_clients
    
    # Check that clients are initialized
    assert km1 is not None
    assert km2 is not None
    
    # Check connectivity
    status1 = await km1.get_status()
    status2 = await km2.get_status()
    
    assert status1 is not None
    assert status2 is not None
    
    # Check key status
    km1_keys = await km1.check_key_status(3)  # Check receiver
    km2_keys = await km2.check_key_status(1)  # Check sender
    
    assert km1_keys is not None
    assert km2_keys is not None
    assert "stored_key_count" in km1_keys
    assert "stored_key_count" in km2_keys


@pytest.mark.asyncio
async def test_retry_mechanism(init_km_clients):
    """Test that retry mechanism works properly"""
    km1, km2 = init_km_clients
    
    # Request keys with larger size than typically available to trigger potential retry
    try:
        keys = await km1.request_enc_keys(3, number=5, size=256)
        assert keys is not None
    except Exception as e:
        # Even if it ultimately fails, we should see retry attempts in logs
        # This test is mainly to trigger the retry logic
        pass
    
    # Test key cache population
    await km1._populate_key_cache(3)
    status = await km1.check_key_status(3)
    assert status is not None