"""
Mock Quantum Key Management (KM) Server
Simulates a KM server with 1000 pre-generated keys and automatic key regeneration
"""

import asyncio
import base64
import logging
import os
import uuid
from typing import Dict, List, Any, Optional
import json
import time

logger = logging.getLogger(__name__)

class MockKMServer:
    """
    Mock KM server that simulates the real KM server behavior
    with pre-generated keys and automatic key regeneration
    """
    
    def __init__(self, kme_id: int, sae_id: int, key_size: int = 256, initial_keys: int = 1000):
        """Initialize the mock KM server with pre-generated keys"""
        self.kme_id = kme_id
        self.sae_id = sae_id
        self.key_size = key_size  # Key size in bits
        self.key_byte_size = key_size // 8  # Convert to bytes
        self.max_keys = initial_keys
        self.max_key_per_request = 100
        
        # Initialize key storage for each potential peer SAE
        # Dict structure: {peer_sae_id: {key_id: {"key": base64_key, "consumed": bool}}}
        self.key_storage = {}
        
        # Generate initial keys
        self.last_regeneration = time.time()
        logger.info(f"Initializing MockKMServer {kme_id} for SAE {sae_id} with {initial_keys} keys")
    
    def _generate_key(self) -> bytes:
        """Generate a quantum-like key of the specified size"""
        return os.urandom(self.key_byte_size)
    
    def _get_peer_storage(self, peer_sae_id: int) -> Dict[str, Dict[str, Any]]:
        """Get or create key storage for a specific peer SAE ID"""
        if peer_sae_id not in self.key_storage:
            # Initialize storage for this peer
            self.key_storage[peer_sae_id] = {}
            
            # Generate initial keys
            for _ in range(self.max_keys):
                key_id = str(uuid.uuid4())
                key_data = self._generate_key()
                self.key_storage[peer_sae_id][key_id] = {
                    "key": base64.b64encode(key_data).decode(),
                    "consumed": False,
                    "created": time.time()
                }
            logger.info(f"Generated {self.max_keys} initial keys for peer SAE {peer_sae_id}")
        
        return self.key_storage[peer_sae_id]
    
    def _regenerate_keys_if_needed(self, peer_sae_id: int) -> int:
        """Regenerate keys if too many have been consumed"""
        peer_storage = self._get_peer_storage(peer_sae_id)
        
        # Count unconsumed keys
        available_keys = sum(1 for k in peer_storage.values() if not k["consumed"])
        
        # Regenerate if less than 20% keys available
        if available_keys < (self.max_keys * 0.2):
            logger.info(f"Regenerating keys for peer SAE {peer_sae_id}, only {available_keys} keys left")
            
            # Remove consumed keys
            self.key_storage[peer_sae_id] = {
                k_id: k_data for k_id, k_data in peer_storage.items() 
                if not k_data["consumed"]
            }
            
            # Generate new keys to fill back up
            new_keys_needed = self.max_keys - len(self.key_storage[peer_sae_id])
            for _ in range(new_keys_needed):
                key_id = str(uuid.uuid4())
                key_data = self._generate_key()
                self.key_storage[peer_sae_id][key_id] = {
                    "key": base64.b64encode(key_data).decode(),
                    "consumed": False,
                    "created": time.time()
                }
            
            self.last_regeneration = time.time()
            logger.info(f"Regenerated {new_keys_needed} keys for peer SAE {peer_sae_id}")
        
        return sum(1 for k in self._get_peer_storage(peer_sae_id).values() if not k["consumed"])
    
    def get_sae_info(self) -> Dict[str, Any]:
        """Get information about this SAE"""
        return {
            "SAE_ID": self.sae_id,
            "KME_ID": self.kme_id
        }
    
    def get_key_status(self, peer_sae_id: int) -> Dict[str, Any]:
        """Get key status for a specific peer SAE ID"""
        # Ensure keys exist and regenerate if needed
        available_count = self._regenerate_keys_if_needed(peer_sae_id)
        
        return {
            "source_KME_ID": str(self.kme_id),
            "target_KME_ID": str(3 - self.kme_id),  # If KME is 1, target is 2 and vice versa
            "master_SAE_ID": str(self.sae_id),
            "slave_SAE_ID": str(peer_sae_id),
            "key_size": self.key_size,
            "stored_key_count": available_count,
            "max_key_count": self.max_keys,
            "max_key_per_request": self.max_key_per_request,
            "max_key_size": self.key_size,
            "min_key_size": self.key_size,
            "max_SAE_ID_count": 0
        }
    
    def request_enc_keys(self, peer_sae_id: int, number: int = 1) -> List[Dict[str, Any]]:
        """Request encryption keys for a specific peer SAE ID"""
        peer_storage = self._get_peer_storage(peer_sae_id)
        
        # Regenerate keys if needed
        self._regenerate_keys_if_needed(peer_sae_id)
        
        # Find unconsumed keys
        available_keys = [
            (key_id, key_data) for key_id, key_data in peer_storage.items()
            if not key_data["consumed"]
        ]
        
        if len(available_keys) < number:
            logger.warning(f"Not enough keys available: requested {number}, have {len(available_keys)}")
            number = len(available_keys)
        
        # Select keys
        selected_keys = available_keys[:number]
        
        # Format response
        result = []
        for key_id, key_data in selected_keys:
            result.append({
                "key_ID": key_id,
                "key": key_data["key"],
                "key_size": self.key_size
            })
        
        logger.info(f"Provided {len(result)} encryption keys for peer SAE {peer_sae_id}")
        return result
    
    def request_dec_keys(self, peer_sae_id: int, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys by key IDs"""
        peer_storage = self._get_peer_storage(peer_sae_id)
        
        result = []
        for key_id in key_ids:
            if key_id in peer_storage and not peer_storage[key_id]["consumed"]:
                result.append({
                    "key_ID": key_id,
                    "key": peer_storage[key_id]["key"],
                    "key_size": self.key_size
                })
        
        logger.info(f"Provided {len(result)} decryption keys for peer SAE {peer_sae_id}")
        return result
    
    def mark_key_consumed(self, key_id: str, peer_sae_id: Optional[int] = None) -> bool:
        """Mark a key as consumed"""
        # If peer_sae_id not specified, search all peers
        if peer_sae_id is not None:
            peer_storages = [self._get_peer_storage(peer_sae_id)]
        else:
            peer_storages = [self._get_peer_storage(p_id) for p_id in self.key_storage.keys()]
        
        # Try to find and mark the key
        for peer_storage in peer_storages:
            if key_id in peer_storage and not peer_storage[key_id]["consumed"]:
                peer_storage[key_id]["consumed"] = True
                logger.info(f"Marked key {key_id} as consumed")
                return True
        
        logger.warning(f"Key {key_id} not found or already consumed")
        return False
    
    def get_entropy(self) -> Dict[str, float]:
        """Get entropy information"""
        # Calculate a realistic entropy value based on key size
        # Real quantum entropy would be much more complex to simulate
        return {
            "total_entropy": 7.9 + (hash(time.time()) % 100) / 1000  # Slight variation for realism
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall KM server status"""
        # Count total keys across all peers
        total_keys = 0
        unconsumed_keys = 0
        
        for peer_id, peer_storage in self.key_storage.items():
            total_keys += len(peer_storage)
            unconsumed_keys += sum(1 for k in peer_storage.values() if not k["consumed"])
        
        return {
            "healthy": True,
            "kme_id": self.kme_id,
            "sae_id": self.sae_id,
            "uptime": time.time() - self.last_regeneration,
            "total_keys": total_keys,
            "available_keys": unconsumed_keys,
            "entropy": 7.9 + (hash(time.time()) % 100) / 1000
        }


# Create global mock KM server instances
mock_km1_server = MockKMServer(kme_id=1, sae_id=1)  # Alice's KM server (KME 1)
mock_km2_server = MockKMServer(kme_id=2, sae_id=3)  # Bob's KM server (KME 2)

# Access functions for the global instances
def get_mock_km1() -> MockKMServer:
    return mock_km1_server

def get_mock_km2() -> MockKMServer:
    return mock_km2_server
