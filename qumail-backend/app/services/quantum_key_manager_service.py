"""
Quantum Key Manager Service
Production-ready service for managing quantum key lifecycle with KME integration
"""
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..mongo_models importquantum_key import QuantumKey, KeyState
from ..services.km_client_init import get_optimized_km_clients


logger = logging.getLogger(__name__)


class QuantumKeyManager:
    """
    Enterprise-grade quantum key management with full lifecycle tracking
    """
    
    # KME SAE IDs for Next Door Key Simulator
    KME1_SAE_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"
    KME2_SAE_ID = "25840139-0dd4-49ae-ba1e-b86731601803"
    
    # Key expiration settings
    KEY_RESERVATION_TIMEOUT = timedelta(minutes=5)
    KEY_EXPIRATION_TIME = timedelta(hours=24)
    
    def __init__(self):
        self.km1_client, self.km2_client = get_optimized_km_clients()
    
    async def generate_and_store_key(
        self, 
        required_bits: int,
        db: AsyncSession
    ) -> QuantumKey:
        """
        Generate quantum keys from both KME servers and store in database
        
        Args:
            required_bits: Minimum key size in bits
            db: Database session
            
        Returns:
            QuantumKey object with stored keys
            
        Raises:
            RuntimeError: If key generation fails
        """
        try:
            logger.info(f"Generating quantum keys: {required_bits} bits required")
            
            # Check key availability on KME1
            logger.debug(f"Checking key availability on KME1 (SAE: {self.KME1_SAE_ID})")
            km1_status = await self.km1_client.check_key_status(self.KME1_SAE_ID)
            available_keys = km1_status.get("stored_key_count", 0)
            
            if available_keys < 1:
                raise RuntimeError(
                    f"Insufficient quantum keys on KME1: {available_keys} available, need at least 1"
                )
            
            logger.info(f"KME1 has {available_keys} keys available")
            
            # Request keys from both KMEs
            logger.info(f"Requesting quantum key from KME1 (SAE: {self.KME1_SAE_ID})")
            km1_result = await self.km1_client.get_key_with_key_ids(
                slave_sae_id=self.KME1_SAE_ID,
                key_size=max(required_bits, 256),
                number=1
            )
            
            if not km1_result.get("keys") or len(km1_result["keys"]) == 0:
                raise RuntimeError("KME1 returned no keys")
            
            km1_key_data = km1_result["keys"][0]
            logger.info(f"KME1 key received: ID={km1_key_data['key_ID']}, size={km1_key_data.get('key_size_bits', 'unknown')} bits")
            
            logger.info(f"Requesting quantum key from KME2 (SAE: {self.KME2_SAE_ID})")
            km2_result = await self.km2_client.get_key_with_key_ids(
                slave_sae_id=self.KME2_SAE_ID,
                key_size=max(required_bits, 256),
                number=1
            )
            
            if not km2_result.get("keys") or len(km2_result["keys"]) == 0:
                raise RuntimeError("KME2 returned no keys")
            
            km2_key_data = km2_result["keys"][0]
            logger.info(f"KME2 key received: ID={km2_key_data['key_ID']}, size={km2_key_data.get('key_size_bits', 'unknown')} bits")
            
            # Decode key material
            km1_key_material = base64.b64decode(km1_key_data["key"])
            km2_key_material = base64.b64decode(km2_key_data["key"])
            
            # Create database record
            quantum_key = QuantumKey(
                kme1_key_id=km1_key_data["key_ID"],
                kme2_key_id=km2_key_data["key_ID"],
                kme1_key_material=km1_key_material,
                kme2_key_material=km2_key_material,
                key_size_bits=len(km1_key_material) * 8,
                algorithm="OTP-QKD",
                state=KeyState.STORED,
                source_kme1_sae=self.KME1_SAE_ID,
                source_kme2_sae=self.KME2_SAE_ID,
                generated_at=datetime.utcnow()
            )
            
            db.add(quantum_key)
            await db.flush()
            
            logger.info(f"Quantum key stored in database: {quantum_key.id}")
            logger.info(f"  - KME1 Key ID: {quantum_key.kme1_key_id}")
            logger.info(f"  - KME2 Key ID: {quantum_key.kme2_key_id}")
            logger.info(f"  - Key Size: {quantum_key.key_size_bits} bits ({len(km1_key_material)} bytes)")
            
            return quantum_key
            
        except Exception as e:
            logger.error(f"Failed to generate and store quantum key: {e}")
            raise RuntimeError(f"Quantum key generation failed: {e}")
    
    async def reserve_key_for_encryption(
        self,
        required_bytes: int,
        user_email: str,
        flow_id: str,
        db: AsyncSession
    ) -> QuantumKey:
        """
        Reserve an available quantum key for encryption
        
        Args:
            required_bytes: Minimum key size in bytes
            user_email: Email of user reserving the key
            flow_id: Email flow ID
            db: Database session
            
        Returns:
            Reserved QuantumKey
            
        Raises:
            RuntimeError: If no suitable key is available
        """
        try:
            # First try to find an existing stored key
            result = await db.execute(
                select(QuantumKey)
                .where(
                    and_(
                        QuantumKey.state == KeyState.STORED,
                        QuantumKey.key_size_bits >= required_bytes * 8
                    )
                )
                .limit(1)
            )
            
            quantum_key = result.scalar_one_or_none()
            
            # If no key available, generate a new one
            if not quantum_key:
                logger.info(f"No stored quantum key available, generating new key for {required_bytes} bytes")
                quantum_key = await self.generate_and_store_key(required_bytes * 8, db)
            
            # Reserve the key
            quantum_key.state = KeyState.RESERVED
            quantum_key.reserved_at = datetime.utcnow()
            quantum_key.used_by_email = user_email
            quantum_key.used_for_flow_id = flow_id
            
            await db.flush()
            
            logger.info(f"Quantum key reserved: {quantum_key.id} for flow {flow_id}")
            
            return quantum_key
            
        except Exception as e:
            logger.error(f"Failed to reserve quantum key: {e}")
            raise RuntimeError(f"Key reservation failed: {e}")
    
    async def consume_key(
        self,
        key_id: str,
        db: AsyncSession
    ) -> None:
        """
        Mark a quantum key as consumed (one-time pad principle)
        
        Args:
            key_id: ID of the quantum key
            db: Database session
        """
        try:
            result = await db.execute(
                select(QuantumKey).where(QuantumKey.id == key_id)
            )
            quantum_key = result.scalar_one_or_none()
            
            if not quantum_key:
                logger.warning(f"Quantum key not found for consumption: {key_id}")
                return
            
            quantum_key.state = KeyState.CONSUMED
            quantum_key.consumed_at = datetime.utcnow()
            
            await db.flush()
            
            logger.info(f"Quantum key consumed: {key_id}")
            
        except Exception as e:
            logger.error(f"Failed to consume quantum key {key_id}: {e}")
    
    async def get_key_for_decryption(
        self,
        kme1_key_id: str,
        kme2_key_id: str,
        db: AsyncSession
    ) -> Tuple[bytes, bytes]:
        """
        Retrieve quantum key material for decryption
        
        Args:
            kme1_key_id: KME1 key identifier
            kme2_key_id: KME2 key identifier
            db: Database session
            
        Returns:
            Tuple of (kme1_key_material, kme2_key_material)
            
        Raises:
            RuntimeError: If keys not found
        """
        try:
            result = await db.execute(
                select(QuantumKey).where(
                    and_(
                        QuantumKey.kme1_key_id == kme1_key_id,
                        QuantumKey.kme2_key_id == kme2_key_id
                    )
                )
            )
            
            quantum_key = result.scalar_one_or_none()
            
            if not quantum_key:
                raise RuntimeError(
                    f"Quantum keys not found: KME1={kme1_key_id}, KME2={kme2_key_id}"
                )
            
            logger.info(f"Retrieved quantum key for decryption: {quantum_key.id}")
            logger.info(f"  - State: {quantum_key.state.value}")
            logger.info(f"  - Generated: {quantum_key.generated_at}")
            
            return quantum_key.kme1_key_material, quantum_key.kme2_key_material
            
        except Exception as e:
            logger.error(f"Failed to retrieve quantum keys for decryption: {e}")
            raise RuntimeError(f"Key retrieval failed: {e}")
    
    async def cleanup_expired_keys(self, db: AsyncSession) -> int:
        """
        Clean up expired/stale quantum keys
        
        Args:
            db: Database session
            
        Returns:
            Number of keys cleaned up
        """
        try:
            expiration_time = datetime.utcnow() - self.KEY_EXPIRATION_TIME
            
            result = await db.execute(
                select(QuantumKey).where(
                    and_(
                        QuantumKey.state.in_([KeyState.STORED, KeyState.RESERVED]),
                        QuantumKey.generated_at < expiration_time
                    )
                )
            )
            
            expired_keys = result.scalars().all()
            count = 0
            
            for key in expired_keys:
                key.state = KeyState.EXPIRED
                count += 1
            
            if count > 0:
                await db.flush()
                logger.info(f"Marked {count} quantum keys as expired")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0


# Global quantum key manager instance
quantum_key_manager = QuantumKeyManager()
