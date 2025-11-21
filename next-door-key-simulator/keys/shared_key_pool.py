"""
Shared Key Pool for KME1 and KME2

KME1: Master - Generates keys and stores in shared pool
KME2: Slave - Retrieves keys from shared pool (doesn't generate)

Both KMEs access the same pool using a centralized pool server
"""
import json
import os
import threading
import time
import requests
from typing import Optional, Dict, Any, List

from keys.key_generator import KeyGenerator


class SharedKeyPoolServer:
    """
    Centralized shared pool server
    Only runs on KME1 - generates and stores keys for both KMEs
    """
    
    def __init__(self):
        self.keys: List[Dict[str, str]] = []
        self.reserved_keys: Dict[str, Dict[str, str]] = {}  # Keys reserved for encryption but not yet consumed
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.stop = threading.Event()
        
        # Configuration
        self.default_key_size = int(os.getenv('DEFAULT_KEY_SIZE', '32'))
        self.max_key_count = int(os.getenv('MAX_KEY_COUNT', '1000'))
        self.generate_interval = float(os.getenv('KEY_GEN_SEC_TO_GEN', '1.0'))
        self.batch_size = int(os.getenv('KEY_GEN_BATCH_SIZE', '100'))
        self.refill_threshold = int(os.getenv('REFILL_THRESHOLD', '500'))
        self.persistence_file = "pool_keys.json"
        
        # Statistics
        self.total_generated = 0
        self.total_retrieved = 0
        self.kme1_retrieved = 0
        self.kme2_retrieved = 0
        
        # Load keys from disk if available
        self._load_keys()
        
        print(f"[SHARED POOL] Initialized: max={self.max_key_count}, batch={self.batch_size}, threshold={self.refill_threshold}")
    
    def _load_keys(self):
        """Load keys from persistence file"""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.keys = data.get('keys', [])
                    self.total_generated = data.get('total_generated', 0)
                    self.total_retrieved = data.get('total_retrieved', 0)
                    print(f"[SHARED POOL] Loaded {len(self.keys)} keys from {self.persistence_file}")
        except Exception as e:
            print(f"[SHARED POOL] Failed to load keys: {e}")

    def _save_keys(self):
        """Save keys to persistence file"""
        try:
            data = {
                'keys': self.keys,
                'total_generated': self.total_generated,
                'total_retrieved': self.total_retrieved,
                'timestamp': time.time()
            }
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[SHARED POOL] Failed to save keys: {e}")

    def _generate_key_unlocked(self) -> Dict[str, str]:
        """Generate a single key (must be called with lock held)"""
        key = KeyGenerator.generate_key(self.default_key_size)
        self.total_generated += 1
        return key
    
    def add_keys_batch(self, count: int) -> int:
        """
        Add multiple keys to pool
        Returns: Number of keys actually added
        """
        with self.condition:
            remaining_capacity = self.max_key_count - len(self.keys)
            to_generate = min(count, remaining_capacity)
            
            if to_generate > 0:
                for _ in range(to_generate):
                    self.keys.append(self._generate_key_unlocked())
                
                self._save_keys()  # Save after generation
                self.condition.notify_all()
                print(f"[SHARED POOL] Generated {to_generate} keys, pool now has {len(self.keys)}/{self.max_key_count} keys")
            
            return to_generate
    
    def get_keys(self, count: int, kme_id: str, timeout: float = 10.0, remove: bool = False) -> List[Dict[str, str]]:
        """
        Retrieve keys from shared pool
        
        Args:
            count: Number of keys requested
            kme_id: Which KME is requesting (for statistics)
            timeout: Max wait time in seconds
            remove: Whether to remove keys from pool (False for encryption, True for cleanup)
        
        Returns:
            List of keys (may be less than requested if timeout)
        """
        start_time = time.time()
        keys_retrieved = []
        modified = False
        
        with self.condition:
            while len(keys_retrieved) < count:
                # Check if we have keys available
                if len(self.keys) > 0:
                    if remove:
                        # Remove key from pool (for cleanup/testing)
                        key = self.keys.pop(0)
                        modified = True
                    else:
                        # Reserve key for encryption - move to reserved dict
                        # Key will be removed from pool but kept in reserved until dec_keys
                        key = self.keys.pop(0)
                        key_copy = key.copy()
                        self.reserved_keys[key['key_ID']] = key  # Store original in reserved
                        modified = True
                    
                    keys_retrieved.append(key if remove else key_copy)
                    print(f"[SHARED POOL] KME{kme_id} retrieved key {key['key_ID'][:16]}..., remove={remove}, reserved={not remove}")
                    
                    if remove:
                        self.total_retrieved += 1
                        if kme_id == "1":
                            self.kme1_retrieved += 1
                        elif kme_id == "2":
                            self.kme2_retrieved += 1
                else:
                    # Pool empty - wait for generation
                    elapsed = time.time() - start_time
                    remaining_timeout = timeout - elapsed
                    
                    if remaining_timeout <= 0:
                        print(f"[SHARED POOL] WARNING: Timeout waiting for keys, got {len(keys_retrieved)}/{count} for KME{kme_id}")
                        break
                    
                    self.condition.wait(timeout=remaining_timeout)
            
            if modified:
                self._save_keys()
            
            action = "removed" if remove else f"reserved (moved to reserved_keys, {len(self.reserved_keys)} total reserved)"
            print(f"[SHARED POOL] KME{kme_id} {action} {len(keys_retrieved)} keys, pool has {len(self.keys)} available keys")
        
        return keys_retrieved
    
    def get_key_by_id(self, key_id: str, kme_id: str, remove: bool = True) -> Optional[Dict[str, str]]:
        """
        Retrieve specific key by ID
        
        Args:
            key_id: The key ID to retrieve
            kme_id: Which KME is requesting
            remove: Whether to remove the key from pool (default True for OTP)
        
        Returns:
            Key dict or None if not found
        """
        with self.condition:
            # First check reserved keys (keys used for encryption but not yet consumed)
            if key_id in self.reserved_keys:
                found_key = self.reserved_keys[key_id]
                
                if remove:
                    # OTP consumption - remove from reserved
                    del self.reserved_keys[key_id]
                    self.total_retrieved += 1
                    
                    if kme_id == "1":
                        self.kme1_retrieved += 1
                    elif kme_id == "2":
                        self.kme2_retrieved += 1
                    
                    self._save_keys()
                    print(f"[SHARED POOL] KME{kme_id} consumed reserved key: {key_id[:16]}..., {len(self.reserved_keys)} reserved keys remaining")
                    return found_key
                else:
                    # Just return copy without removing
                    print(f"[SHARED POOL] KME{kme_id} read reserved key (not removed): {key_id[:16]}...")
                    return found_key.copy()
            
            # Check available keys pool
            for i, key in enumerate(self.keys):
                if key['key_ID'] == key_id:
                    if remove:
                        # OTP mode - remove after retrieval
                        found_key = self.keys.pop(i)
                        self.total_retrieved += 1
                        
                        if kme_id == "1":
                            self.kme1_retrieved += 1
                        elif kme_id == "2":
                            self.kme2_retrieved += 1
                        
                        self._save_keys()
                        print(f"[SHARED POOL] KME{kme_id} retrieved and removed key from available pool: {key_id[:16]}..., {len(self.keys)} keys remaining")
                        return found_key
                    else:
                        # Non-OTP mode - just return copy without removing
                        print(f"[SHARED POOL] KME{kme_id} read key from available pool (not removed): {key_id[:16]}...")
                        return key.copy()
            
            print(f"[SHARED POOL] WARNING: Key ID {key_id[:16]}... not found in pool or reserved keys")
            print(f"[SHARED POOL] DEBUG: Available keys={len(self.keys)}, Reserved keys={len(self.reserved_keys)}")
            if len(self.reserved_keys) > 0:
                sample_reserved = list(self.reserved_keys.keys())[:5]
                print(f"[SHARED POOL] DEBUG: Sample reserved key IDs: {[kid[:16] for kid in sample_reserved]}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get pool status and statistics"""
        with self.condition:
            return {
                "pool_size": len(self.keys),
                "reserved_keys": len(self.reserved_keys),
                "total_available": len(self.keys) + len(self.reserved_keys),
                "max_capacity": self.max_key_count,
                "total_generated": self.total_generated,
                "total_retrieved": self.total_retrieved,
                "kme1_retrieved": self.kme1_retrieved,
                "kme2_retrieved": self.kme2_retrieved,
                "utilization": (len(self.keys) + len(self.reserved_keys)) / self.max_key_count * 100 if self.max_key_count > 0 else 0
            }
    
    def start_generation(self):
        """Start background key generation loop"""
        print("[SHARED POOL] Starting background generation thread")
        
        while not self.stop.is_set():
            try:
                with self.condition:
                    current_count = len(self.keys)
                    remaining_capacity = self.max_key_count - current_count
                    
                    # Generate if below threshold
                    if current_count < self.refill_threshold and remaining_capacity > 0:
                        batch_count = min(self.batch_size, remaining_capacity)
                        
                        print(f"[SHARED POOL] Generating batch: {batch_count} keys (pool={current_count}/{self.max_key_count})")
                        
                        for _ in range(batch_count):
                            self.keys.append(self._generate_key_unlocked())
                        
                        self.total_generated += batch_count
                        self.condition.notify_all()
                        
                        print(f"[SHARED POOL] Generated {batch_count} keys, pool now has {len(self.keys)} keys")
                
                # Sleep before next generation cycle
                self.stop.wait(timeout=self.generate_interval)
                
            except Exception as e:
                print(f"[SHARED POOL] ERROR in generation loop: {e}")
                time.sleep(1)
        
        print("[SHARED POOL] Generation thread stopped")


class SharedKeyPoolClient:
    """
    Client for accessing shared pool from KME1 or KME2
    KME1: Direct access to local pool
    KME2: Fetches keys from KME1 via HTTP
    """
    
    def __init__(self, pool_server: SharedKeyPoolServer, kme_id: str):
        self.pool_server = pool_server
        self.kme_id = kme_id
        self.lock = threading.Lock()  # For compatibility with existing code
        
        # KME2 needs KME1 URL for HTTP requests
        if kme_id == "2":
            self.kme1_url = os.getenv('OTHER_KMES', 'http://127.0.0.1:8010')
            print(f"[POOL CLIENT] KME{kme_id} initialized - will fetch keys from {self.kme1_url}")
        else:
            self.kme1_url = None
            print(f"[POOL CLIENT] KME{kme_id} initialized - local pool")
    
    def get_key(self, key_size: int, timeout: Optional[float] = None, remove: bool = False) -> Optional[Dict[str, str]]:
        """
        Get a single key from shared pool
        Compatible with original KeyPool.get_key() interface
        
        KME1: Gets from local pool
        KME2: Fetches from KME1 via HTTP
        
        Args:
            key_size: Key size in BITS (will be converted to bytes for generation)
            timeout: Timeout in seconds
            remove: If True, remove from pool (OTP consumption). If False, copy only (for enc_keys).
        """
        configured_timeout = timeout if timeout is not None else 10.0
        
        # Convert bits to bytes for size comparison
        default_size_bits = int(os.getenv('DEFAULT_KEY_SIZE', '32')) * 8  # DEFAULT_KEY_SIZE is in bytes
        
        # For non-default size, generate on-demand
        if key_size and key_size != default_size_bits:
            # Convert bits to bytes (round up)
            key_size_bytes = (key_size + 7) // 8
            print(f'[POOL CLIENT] KME{self.kme_id}: Generating key for non-default size {key_size} bits ({key_size_bytes} bytes)')
            return KeyGenerator.generate_key(key_size_bytes)
        
        # KME2: Fetch from KME1 via HTTP
        if self.kme_id == "2":
            try:
                response = requests.post(
                    f"{self.kme1_url}/api/v1/internal/get_shared_key",
                    json={"kme_id": "2", "count": 1},
                    timeout=configured_timeout,
                    verify=False
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'keys' in data and len(data['keys']) > 0:
                        print(f'[POOL CLIENT] KME2: Retrieved key from KME1')
                        return data['keys'][0]
                    else:
                        print(f'[POOL CLIENT] KME2: No keys available from KME1')
                        return None
                else:
                    print(f'[POOL CLIENT] KME2: HTTP error {response.status_code} from KME1')
                    return None
            except Exception as e:
                print(f'[POOL CLIENT] KME2: Failed to fetch from KME1: {e}')
                return None
        
        # KME1: Get from local pool
        keys = self.pool_server.get_keys(1, self.kme_id, configured_timeout, remove=remove)
        
        if len(keys) > 0:
            return keys[0]
        else:
            print(f'[POOL CLIENT] KME{self.kme_id}: Failed to get key from pool')
            return None
    
    def get_key_by_id(self, key_id: str) -> Optional[Dict[str, str]]:
        """Get specific key by ID"""
        # KME2: Fetch from KME1 via HTTP
        if self.kme_id == "2":
            try:
                # Use configured timeout or default
                timeout = 10.0
                
                print(f"[POOL CLIENT] KME2: Fetching key {key_id[:8]}... from KME1")
                response = requests.post(
                    f"{self.kme1_url}/api/v1/internal/get_reserved_key",
                    json={"key_id": key_id, "kme_id": "2", "remove": True},
                    timeout=timeout,
                    verify=False
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'key' in data:
                        print(f'[POOL CLIENT] KME2: Retrieved key {key_id[:8]}... from KME1')
                        return data['key']
                    else:
                        print(f'[POOL CLIENT] KME2: Key {key_id[:8]}... not found in KME1 response')
                        return None
                else:
                    print(f'[POOL CLIENT] KME2: HTTP error {response.status_code} from KME1 when fetching key {key_id[:8]}...')
                    return None
            except Exception as e:
                print(f'[POOL CLIENT] KME2: Failed to fetch key {key_id[:8]}... from KME1: {e}')
                return None
        
        # KME1: Get from local pool
        return self.pool_server.get_key_by_id(key_id, self.kme_id)
    
    def add_key(self) -> None:
        """
        Add key to pool (for compatibility)
        Only KME1 should call this
        """
        if self.kme_id == "1":
            self.pool_server.add_keys_batch(1)
        else:
            print(f"[POOL CLIENT] WARNING: KME{self.kme_id} tried to add key - only KME1 should generate!")
    
    def start(self) -> None:
        """
        Start generation (for compatibility)
        Only starts if this is KME1
        """
        if self.kme_id == "1":
            print(f"[POOL CLIENT] KME{self.kme_id} starting shared pool generation")
            # This will be called from a separate thread
            self.pool_server.start_generation()
        else:
            print(f"[POOL CLIENT] KME{self.kme_id} is slave - not starting generation")
            # Slave just waits forever (thread needs to stay alive)
            while not self.pool_server.stop.is_set():
                self.pool_server.stop.wait(timeout=10)


# Global shared pool instance
_shared_pool_server: Optional[SharedKeyPoolServer] = None


def get_shared_pool_server() -> SharedKeyPoolServer:
    """Get or create global shared pool server"""
    global _shared_pool_server
    if _shared_pool_server is None:
        _shared_pool_server = SharedKeyPoolServer()
    return _shared_pool_server


def create_pool_client(kme_id: str, gen_lock: threading.Lock) -> SharedKeyPoolClient:
    """
    Create a pool client for a specific KME
    
    Args:
        kme_id: "1" or "2"
        gen_lock: Lock for compatibility (not used with shared pool)
    
    Returns:
        SharedKeyPoolClient instance
    """
    pool_server = get_shared_pool_server()
    return SharedKeyPoolClient(pool_server, kme_id)
