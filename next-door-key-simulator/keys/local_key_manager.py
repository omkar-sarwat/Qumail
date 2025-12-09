"""
Local Key Manager (Local KM) for ETSI GS QKD 014 Compliant QKD System

The Local KM acts as a caching layer between users and the Next Door KM (remote):
- Always available to users (even when Next Door KM is offline)
- Caches per-user key pools locally
- Syncs with Next Door KM periodically or when pools run low
- Follows hybrid sync strategy: daily scheduled + threshold-based emergency sync
"""
import os
import json
import time
import threading
import requests
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from queue import Queue, Empty

from keys.user_key_pool import UserKeyPool, get_user_key_pool, KEY_SIZE_BYTES, KEY_SIZE_BITS


class LocalKeyManager:
    """
    Local Key Manager that caches keys from Next Door KM.
    
    Features:
    - Per-user key pool caching
    - Hybrid sync strategy (scheduled + threshold-based)
    - Graceful handling of Next Door KM unavailability
    - ETSI GS QKD 014 compliant API
    """
    
    def __init__(self, 
                 local_km_id: str = None,
                 next_door_km_url: str = None,
                 db_path: str = None,
                 sync_interval_hours: int = 24,
                 low_threshold_percent: float = 0.10,
                 emergency_threshold_percent: float = 0.05):
        """
        Initialize the Local Key Manager.
        
        Args:
            local_km_id: Unique ID for this Local KM instance
            next_door_km_url: URL of the Next Door KM (remote)
            db_path: Path to local SQLite database
            sync_interval_hours: Hours between scheduled syncs (default: 24)
            low_threshold_percent: Trigger warning at this % remaining (default: 10%)
            emergency_threshold_percent: Trigger emergency sync at this % (default: 5%)
        """
        self.local_km_id = local_km_id or os.getenv('LOCAL_KM_ID', 'LOCAL_KM_001')
        self.next_door_km_url = next_door_km_url or os.getenv('NEXT_DOOR_KM_URL', 'http://localhost:8010')
        self.db_path = db_path or os.getenv('LOCAL_KM_DB', 'local_km.db')
        
        # Sync configuration
        self.sync_interval = timedelta(hours=sync_interval_hours)
        self.low_threshold_percent = low_threshold_percent
        self.emergency_threshold_percent = emergency_threshold_percent
        
        # Initialize user key pool (local cache)
        self.user_pool = get_user_key_pool(self.db_path)
        
        # Sync state
        self.last_sync_time: Optional[datetime] = None
        self.next_sync_time: Optional[datetime] = None
        self.sync_in_progress = False
        self.sync_lock = threading.Lock()
        
        # Background sync thread
        self.stop_event = threading.Event()
        self.sync_queue = Queue()
        self.sync_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'keys_received': 0,
            'next_door_km_available': True
        }
        
        # Initialize sync database table
        self._init_sync_db()
        
        print(f"[LOCAL_KM] Initialized: {self.local_km_id}")
        print(f"[LOCAL_KM] Next Door KM URL: {self.next_door_km_url}")
        print(f"[LOCAL_KM] Sync interval: {sync_interval_hours} hours")
    
    def _init_sync_db(self):
        """Initialize additional tables for sync tracking."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Local KM configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_km_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            
            # Store last sync time
            cursor.execute("""
                INSERT OR REPLACE INTO local_km_config (key, value, updated_at)
                VALUES ('last_sync_time', ?, ?)
            """, (None, datetime.utcnow().isoformat()))
            
            conn.commit()
    
    def start(self):
        """Start the Local KM background services."""
        print(f"[LOCAL_KM] Starting background services...")
        
        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        # Schedule initial sync check
        self._schedule_sync_check()
        
        print(f"[LOCAL_KM] Background services started")
    
    def stop(self):
        """Stop the Local KM background services."""
        print(f"[LOCAL_KM] Stopping...")
        self.stop_event.set()
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print(f"[LOCAL_KM] Stopped")
    
    def _sync_worker(self):
        """Background worker for sync operations."""
        while not self.stop_event.is_set():
            try:
                # Check for sync requests
                try:
                    sync_request = self.sync_queue.get(timeout=60)  # Check every minute
                    if sync_request:
                        self._perform_sync(sync_request.get('users'), sync_request.get('reason'))
                except Empty:
                    pass
                
                # Check if scheduled sync is due
                if self.next_sync_time and datetime.utcnow() >= self.next_sync_time:
                    self._perform_sync(reason='scheduled')
                
                # Check for low pools (threshold-based sync)
                self._check_low_pools()
                
            except Exception as e:
                print(f"[LOCAL_KM] Sync worker error: {e}")
                time.sleep(5)
    
    def _schedule_sync_check(self):
        """Schedule the next sync time."""
        now = datetime.utcnow()
        
        if self.last_sync_time:
            self.next_sync_time = self.last_sync_time + self.sync_interval
            if self.next_sync_time <= now:
                self.next_sync_time = now + timedelta(minutes=5)  # Sync soon
        else:
            # First run - sync in 5 minutes
            self.next_sync_time = now + timedelta(minutes=5)
        
        print(f"[LOCAL_KM] Next scheduled sync: {self.next_sync_time.isoformat()}")
    
    def _check_low_pools(self):
        """Check for pools below threshold and trigger emergency sync."""
        low_pools = self.user_pool.get_low_pools()
        
        if low_pools:
            # Check for emergency threshold (very low pools)
            emergency_pools = []
            for pool in low_pools:
                available = pool['available_keys']
                limit = pool['pool_size_limit']
                percent = available / limit if limit > 0 else 0
                
                if percent < self.emergency_threshold_percent:
                    emergency_pools.append(pool)
            
            if emergency_pools:
                print(f"[LOCAL_KM] EMERGENCY: {len(emergency_pools)} pools critically low!")
                users = [p['sae_id'] for p in emergency_pools]
                self.request_sync(users=users, reason='emergency')
    
    def request_sync(self, users: List[str] = None, reason: str = 'manual'):
        """
        Request a sync with Next Door KM.
        
        Args:
            users: Specific users to sync (None = all users)
            reason: Reason for sync (manual, scheduled, threshold, emergency)
        """
        self.sync_queue.put({'users': users, 'reason': reason})
        print(f"[LOCAL_KM] Sync requested: reason={reason}, users={users}")
    
    def _perform_sync(self, users: List[str] = None, reason: str = 'unknown') -> Dict[str, Any]:
        """
        Perform synchronization with Next Door KM.
        
        Args:
            users: Specific users to sync (None = all users with low pools)
            reason: Reason for sync
        
        Returns:
            Sync result
        """
        with self.sync_lock:
            if self.sync_in_progress:
                return {'success': False, 'error': 'Sync already in progress'}
            self.sync_in_progress = True
        
        start_time = time.time()
        result = {
            'success': False,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'users_synced': 0,
            'keys_received': 0,
            'errors': []
        }
        
        try:
            print(f"[LOCAL_KM] Starting sync: reason={reason}")
            
            # Determine which users need sync
            if users is None:
                # Get all users with low pools
                low_pools = self.user_pool.get_low_pools()
                users = [p['sae_id'] for p in low_pools]
                
                if not users:
                    # No low pools, but if scheduled, do a check anyway
                    if reason == 'scheduled':
                        all_pools = self.user_pool.get_all_pools_status()
                        users = [p['sae_id'] for p in all_pools.get('pools', [])]
            
            if not users:
                result['success'] = True
                result['message'] = 'No users require sync'
                return result
            
            # Build sync request for Next Door KM
            sync_request = {
                'local_km_id': self.local_km_id,
                'users': []
            }
            
            for sae_id in users:
                status = self.user_pool.get_pool_status(sae_id)
                if 'error' not in status:
                    keys_needed = status['pool_size_limit'] - status['available_keys']
                    if keys_needed > 0:
                        sync_request['users'].append({
                            'sae_id': sae_id,
                            'requested_keys': keys_needed
                        })
            
            if not sync_request['users']:
                result['success'] = True
                result['message'] = 'All pools are full'
                return result
            
            # Try to sync with Next Door KM
            try:
                response = requests.post(
                    f"{self.next_door_km_url}/api/v1/keys/sync",
                    json=sync_request,
                    timeout=30
                )
                
                if response.status_code == 200:
                    sync_data = response.json()
                    self.stats['next_door_km_available'] = True
                    
                    # Process received keys
                    for user_sync in sync_data.get('user_syncs', []):
                        sae_id = user_sync.get('sae_id')
                        keys = user_sync.get('keys', [])
                        
                        # Store keys in local pool
                        keys_added = self._store_synced_keys(sae_id, keys)
                        result['keys_received'] += keys_added
                        result['users_synced'] += 1
                    
                    result['success'] = True
                    self.stats['successful_syncs'] += 1
                    self.stats['keys_received'] += result['keys_received']
                    
                else:
                    result['errors'].append(f"Next Door KM returned status {response.status_code}")
                    self.stats['next_door_km_available'] = False
                    self.stats['failed_syncs'] += 1
                    
            except requests.exceptions.RequestException as e:
                result['errors'].append(f"Connection to Next Door KM failed: {e}")
                self.stats['next_door_km_available'] = False
                self.stats['failed_syncs'] += 1
                
                # Fallback: Generate keys locally if Next Door KM unavailable
                if reason == 'emergency':
                    print(f"[LOCAL_KM] Next Door KM unavailable - generating keys locally")
                    for user_req in sync_request['users']:
                        sae_id = user_req['sae_id']
                        requested = user_req['requested_keys']
                        refill_result = self.user_pool.refill_pool(sae_id, requested)
                        if refill_result.get('success'):
                            result['keys_received'] += refill_result.get('keys_added', 0)
                            result['users_synced'] += 1
                    result['success'] = True
                    result['fallback'] = 'local_generation'
            
            # Update sync time
            self.last_sync_time = datetime.utcnow()
            self._schedule_sync_check()
            self.stats['total_syncs'] += 1
            
            # Log sync result
            self._log_sync(result, time.time() - start_time)
            
        except Exception as e:
            result['errors'].append(str(e))
            print(f"[LOCAL_KM] Sync error: {e}")
            
        finally:
            with self.sync_lock:
                self.sync_in_progress = False
        
        duration = time.time() - start_time
        print(f"[LOCAL_KM] Sync complete: {result['users_synced']} users, {result['keys_received']} keys in {duration:.2f}s")
        
        return result
    
    def _store_synced_keys(self, sae_id: str, keys: List[Dict]) -> int:
        """Store keys received from sync into local pool."""
        # For now, just use refill_pool since keys are generated locally
        # In a real implementation, this would store the actual keys from Next Door KM
        return len(keys)
    
    def _log_sync(self, result: Dict, duration: float):
        """Log sync result to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_logs 
                    (sync_time, sync_type, next_door_km_available, users_synced, 
                     total_keys_received, errors, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['timestamp'],
                    result['reason'],
                    1 if self.stats['next_door_km_available'] else 0,
                    result['users_synced'],
                    result['keys_received'],
                    json.dumps(result['errors']),
                    int(duration * 1000)
                ))
                conn.commit()
        except Exception as e:
            print(f"[LOCAL_KM] Failed to log sync: {e}")
    
    # ==================== ETSI GS QKD 014 API Methods ====================
    
    def register_user(self, sae_id: str, user_email: str, 
                      initial_pool_size: int = 1000) -> Dict[str, Any]:
        """
        Register a new user and initialize their key pool.
        ETSI GS QKD 014: POST /api/v1/keys/register
        """
        return self.user_pool.register_user(sae_id, user_email, 
                                            initial_pool_size=initial_pool_size)
    
    def get_enc_keys(self, slave_sae_id: str, master_sae_id: str,
                     number: int = 1, size: int = KEY_SIZE_BYTES,
                     target_user_id: str = None) -> Dict[str, Any]:
        """
        Get encryption keys - sender requests keys from receiver's pool.
        ETSI GS QKD 014: POST /api/v1/keys/{slave_SAE_ID}/enc_keys
        
        Args:
            slave_sae_id: SAE ID in the URL path (typically the receiver)
            master_sae_id: SAE ID of the requester (sender)
            number: Number of keys requested
            size: Key size in bytes (must be 1024)
            target_user_id: Optional explicit target user (receiver)
        
        Returns:
            ETSI formatted response with keys
        """
        # Determine receiver - either from target_user_id or slave_sae_id
        receiver_sae_id = target_user_id or slave_sae_id
        sender_sae_id = master_sae_id
        
        # Validate size
        if size != KEY_SIZE_BYTES:
            return {
                'message': f'Invalid key size. Must be {KEY_SIZE_BYTES} bytes (1KB)',
                'status_code': 400
            }
        
        # Get keys from receiver's pool
        result = self.user_pool.get_keys_for_receiver(
            sender_sae_id=sender_sae_id,
            receiver_sae_id=receiver_sae_id,
            number=number,
            size=size
        )
        
        # Check if pool is getting low after this request
        status = self.user_pool.get_pool_status(receiver_sae_id)
        if status.get('is_low'):
            # Queue a sync for this user
            self.request_sync(users=[receiver_sae_id], reason='threshold')
        
        return result
    
    def get_dec_keys(self, master_sae_id: str, slave_sae_id: str,
                     key_ids: List[str]) -> Dict[str, Any]:
        """
        Get decryption keys by ID.
        ETSI GS QKD 014: POST /api/v1/keys/{master_SAE_ID}/dec_keys
        
        Args:
            master_sae_id: SAE ID in the URL path
            slave_sae_id: SAE ID of the requester
            key_ids: List of key IDs to retrieve
        
        Returns:
            ETSI formatted response with keys
        """
        return self.user_pool.get_keys_by_ids(slave_sae_id, key_ids)
    
    def get_status(self, slave_sae_id: str) -> Dict[str, Any]:
        """
        Get key pool status for a user.
        ETSI GS QKD 014: GET /api/v1/keys/{slave_SAE_ID}/status
        """
        pool_status = self.user_pool.get_pool_status(slave_sae_id)
        
        if 'error' in pool_status:
            return pool_status
        
        # Add ETSI-style fields
        pool_status.update({
            'source_KME_ID': self.local_km_id,
            'key_size': KEY_SIZE_BITS,  # ETSI uses bits
            'max_key_count': pool_status['pool_size_limit'],
            'stored_key_count': pool_status['available_keys'],
            'max_key_per_request': min(100, pool_status['available_keys']),
            'max_key_size': KEY_SIZE_BITS,
            'min_key_size': KEY_SIZE_BITS  # Fixed 1KB keys
        })
        
        return pool_status
    
    def get_km_status(self) -> Dict[str, Any]:
        """Get overall Local KM status."""
        all_pools = self.user_pool.get_all_pools_status()
        
        return {
            'local_km_id': self.local_km_id,
            'next_door_km_url': self.next_door_km_url,
            'next_door_km_available': self.stats['next_door_km_available'],
            'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'next_sync': self.next_sync_time.isoformat() if self.next_sync_time else None,
            'sync_stats': {
                'total': self.stats['total_syncs'],
                'successful': self.stats['successful_syncs'],
                'failed': self.stats['failed_syncs'],
                'keys_received': self.stats['keys_received']
            },
            'pools': all_pools
        }
    
    def force_sync(self, users: List[str] = None) -> Dict[str, Any]:
        """Force immediate sync with Next Door KM."""
        return self._perform_sync(users=users, reason='manual')


# Global instance
_local_km: Optional[LocalKeyManager] = None
_km_lock = threading.Lock()


def get_local_km() -> LocalKeyManager:
    """Get or create the global LocalKeyManager instance."""
    global _local_km
    
    with _km_lock:
        if _local_km is None:
            _local_km = LocalKeyManager()
    
    return _local_km


def start_local_km():
    """Start the Local KM background services."""
    km = get_local_km()
    km.start()
    return km
