"""
ETSI GS QKD 014 REST API Routes for User Key Pools

This module provides REST endpoints that follow the ETSI GS QKD 014 standard
for key delivery between Secure Application Entities (SAEs).

Endpoints:
- POST /api/v1/keys/register - Register user and create key pool
- POST /api/v1/keys/{slave_SAE_ID}/enc_keys - Get encryption keys (from receiver's pool)
- POST /api/v1/keys/{master_SAE_ID}/dec_keys - Get decryption keys by ID
- GET /api/v1/keys/{SAE_ID}/status - Get key pool status
- POST /api/v1/keys/sync - Sync request from Local KM to Next Door KM
- GET /api/v1/keys/pools - Get all pools status (admin)
- POST /api/v1/keys/{SAE_ID}/refill - Refill a user's key pool
"""
import os
import flask
from flask import Blueprint, request, jsonify

from keys.user_key_pool import get_user_key_pool, KEY_SIZE_BYTES, KEY_SIZE_BITS
from keys.local_key_manager import get_local_km


# Create Blueprint for user key routes
# Use /api/v1/user-keys prefix to avoid conflicts with main ETSI QKD 014 routes
user_keys_bp = Blueprint('user_keys', __name__, url_prefix='/api/v1/user-keys')


@user_keys_bp.route('/register', methods=['POST'])
def register_user():
    """
    Register a new user and initialize their key pool.
    
    Request Body:
    {
        "sae_id": "SAE_001",
        "user_email": "alice@example.com",
        "initial_pool_size": 1000  // Optional, default 1000
    }
    
    Response:
    {
        "success": true,
        "sae_id": "SAE_001",
        "pool_size": 1000,
        "keys_generated": 1000
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        sae_id = data.get('sae_id')
        user_email = data.get('user_email')
        initial_pool_size = data.get('initial_pool_size', 1000)
        
        if not sae_id or not user_email:
            return jsonify({'error': 'sae_id and user_email are required'}), 400
        
        local_km = get_local_km()
        result = local_km.register_user(sae_id, user_email, initial_pool_size)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"[USER_KEYS_API] Registration error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/<slave_sae_id>/enc_keys', methods=['GET', 'POST'])
def get_encryption_keys(slave_sae_id: str):
    """
    Get encryption keys from receiver's pool (ETSI GS QKD 014 enc_keys).
    
    CRITICAL: Sender requests keys FROM receiver's pool!
    
    POST Request Body:
    {
        "number": 10,           // Number of keys requested
        "size": 8192,           // Key size in BITS (8192 bits = 1024 bytes)
        "extension_mandatory": {
            "target_user_id": "SAE_002"  // Optional: explicit receiver
        }
    }
    
    Response:
    {
        "keys": [
            {"key_ID": "qk_SAE_002_000001", "key": "base64_encoded_1KB"}
        ]
    }
    """
    try:
        print(f"[USER_KEYS_API] enc_keys called for slave_sae_id={slave_sae_id}")
        local_km = get_local_km()
        
        # Get requester SAE ID (sender) from header or environment
        use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
        
        if use_https:
            # HTTPS mode - get from client certificate
            master_sae_id = request.environ.get('client_cert_common_name', '')
        else:
            # HTTP mode - get from header or query param
            master_sae_id = request.headers.get('X-SAE-ID', 
                            request.args.get('master_sae_id',
                            os.getenv('ATTACHED_SAE_ID', 'UNKNOWN')))
        
        if request.method == 'POST':
            data = request.get_json() or {}
            
            number = data.get('number', 1)
            # ETSI uses BITS, convert to bytes
            size_bits = data.get('size', KEY_SIZE_BITS)
            size_bytes = size_bits // 8
            
            # Get target user ID from extension_mandatory if provided
            extension = data.get('extension_mandatory', {})
            target_user_id = extension.get('target_user_id')
        else:
            # GET request
            number = int(request.args.get('number', 1))
            size_bytes = KEY_SIZE_BYTES
            target_user_id = request.args.get('target_user_id')
        
        # Validate number of keys
        max_keys = int(os.getenv('MAX_KEYS_PER_REQUEST', '100'))
        if number > max_keys:
            return jsonify({
                'message': f'Number of requested keys exceeds max ({max_keys})'
            }), 400
        
        # Get keys from receiver's pool
        result = local_km.get_enc_keys(
            slave_sae_id=slave_sae_id,
            master_sae_id=master_sae_id,
            number=number,
            size=size_bytes,
            target_user_id=target_user_id
        )
        
        if 'error' in result:
            status_code = result.pop('status_code', 400)
            return jsonify(result), status_code
        
        return jsonify({'keys': result.get('keys', [])})
        
    except Exception as e:
        print(f"[USER_KEYS_API] enc_keys error: {e}")
        return jsonify({'message': str(e)}), 500


@user_keys_bp.route('/<master_sae_id>/dec_keys', methods=['GET', 'POST'])
def get_decryption_keys(master_sae_id: str):
    """
    Get decryption keys by their IDs (ETSI GS QKD 014 dec_keys).
    
    POST Request Body:
    {
        "key_IDs": [
            {"key_ID": "qk_SAE_002_000001"},
            {"key_ID": "qk_SAE_002_000002"}
        ]
    }
    
    GET Request:
    ?key_ID=qk_SAE_002_000001&key_ID=qk_SAE_002_000002
    
    Response:
    {
        "keys": [
            {"key_ID": "qk_SAE_002_000001", "key": "base64_encoded_1KB"}
        ]
    }
    """
    try:
        local_km = get_local_km()
        
        # Get requester SAE ID from header
        use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
        
        if use_https:
            slave_sae_id = request.environ.get('client_cert_common_name', '')
        else:
            slave_sae_id = request.headers.get('X-SAE-ID',
                          request.args.get('slave_sae_id',
                          os.getenv('ATTACHED_SAE_ID', 'UNKNOWN')))
        
        if request.method == 'POST':
            data = request.get_json() or {}
            key_ids_list = data.get('key_IDs', [])
            key_ids = [item.get('key_ID') for item in key_ids_list if item.get('key_ID')]
        else:
            # GET request - support both repeated params and comma-separated
            key_id_params = request.args.getlist('key_ID')
            key_ids = []
            for param in key_id_params:
                key_ids.extend(param.split(','))
        
        if not key_ids:
            return jsonify({
                'message': 'No key IDs provided',
                'keys': []
            }), 400
        
        result = local_km.get_dec_keys(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            key_ids=key_ids
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[USER_KEYS_API] dec_keys error: {e}")
        return jsonify({'message': str(e), 'keys': []}), 500


@user_keys_bp.route('/<sae_id>/status', methods=['GET'])
def get_pool_status(sae_id: str):
    """
    Get key pool status for a user (ETSI GS QKD 014 status).
    
    Response:
    {
        "sae_id": "SAE_001",
        "total_keys": 1000,
        "used_keys": 150,
        "available_keys": 850,
        "key_size": 8192,  // bits
        "stored_key_count": 850,
        "max_key_count": 1000
    }
    """
    try:
        print(f"[USER_KEYS_API] status called for sae_id={sae_id}")
        local_km = get_local_km()
        result = local_km.get_status(sae_id)
        print(f"[USER_KEYS_API] status result: available_keys={result.get('available_keys')}")
        
        if 'error' in result:
            status_code = result.pop('status_code', 404)
            return jsonify(result), status_code
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[USER_KEYS_API] status error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/sync', methods=['POST'])
def sync_keys():
    """
    Sync request from Local KM to Next Door KM (or handle incoming sync).
    
    Request Body:
    {
        "local_km_id": "LOCAL_KM_001",
        "users": [
            {"sae_id": "SAE_001", "requested_keys": 500},
            {"sae_id": "SAE_002", "requested_keys": 300}
        ]
    }
    
    Response:
    {
        "success": true,
        "synced_users": 2,
        "total_keys_delivered": 800,
        "user_syncs": [
            {"sae_id": "SAE_001", "keys_delivered": 500},
            {"sae_id": "SAE_002", "keys_delivered": 300}
        ]
    }
    """
    try:
        data = request.get_json() or {}
        
        local_km_id = data.get('local_km_id')
        users_requests = data.get('users', [])
        
        if not users_requests:
            return jsonify({'error': 'No users specified for sync'}), 400
        
        user_pool = get_user_key_pool()
        user_syncs = []
        total_keys = 0
        
        for user_req in users_requests:
            sae_id = user_req.get('sae_id')
            requested = user_req.get('requested_keys', 0)
            
            if sae_id and requested > 0:
                # Refill the user's pool
                result = user_pool.refill_pool(sae_id, requested)
                
                if result.get('success'):
                    keys_added = result.get('keys_added', 0)
                    user_syncs.append({
                        'sae_id': sae_id,
                        'keys_delivered': keys_added,
                        'keys': []  # In real impl, return actual key data
                    })
                    total_keys += keys_added
                else:
                    user_syncs.append({
                        'sae_id': sae_id,
                        'keys_delivered': 0,
                        'error': result.get('error')
                    })
        
        return jsonify({
            'success': True,
            'synced_users': len([u for u in user_syncs if u.get('keys_delivered', 0) > 0]),
            'total_keys_delivered': total_keys,
            'user_syncs': user_syncs,
            'timestamp': flask.g.get('request_time', '')
        })
        
    except Exception as e:
        print(f"[USER_KEYS_API] sync error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/pools', methods=['GET'])
def get_all_pools():
    """
    Get status of all user key pools (admin endpoint).
    
    Response:
    {
        "pools": [...],
        "summary": {
            "total_users": 5,
            "total_keys": 5000,
            "total_available": 4500,
            "low_pool_count": 1
        }
    }
    """
    try:
        user_pool = get_user_key_pool()
        result = user_pool.get_all_pools_status()
        return jsonify(result)
        
    except Exception as e:
        print(f"[USER_KEYS_API] pools error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/<sae_id>/refill', methods=['POST'])
def refill_pool(sae_id: str):
    """
    Manually refill a user's key pool.
    
    Request Body:
    {
        "keys_to_add": 500  // Optional, default fills to limit
    }
    
    Response:
    {
        "success": true,
        "sae_id": "SAE_001",
        "keys_added": 500,
        "available_after": 1000
    }
    """
    try:
        data = request.get_json() or {}
        keys_to_add = data.get('keys_to_add')
        
        user_pool = get_user_key_pool()
        result = user_pool.refill_pool(sae_id, keys_to_add)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"[USER_KEYS_API] refill error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/<sae_id>', methods=['DELETE'])
def delete_user(sae_id: str):
    """
    Delete a user and all their keys.
    
    Response:
    {
        "success": true,
        "sae_id": "SAE_001",
        "keys_deleted": 1000
    }
    """
    try:
        user_pool = get_user_key_pool()
        result = user_pool.delete_user(sae_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"[USER_KEYS_API] delete error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/km/status', methods=['GET'])
def get_km_status():
    """
    Get overall Local Key Manager status.
    
    Response:
    {
        "local_km_id": "LOCAL_KM_001",
        "next_door_km_available": true,
        "sync_stats": {...},
        "pools": {...}
    }
    """
    try:
        local_km = get_local_km()
        result = local_km.get_km_status()
        return jsonify(result)
        
    except Exception as e:
        print(f"[USER_KEYS_API] km status error: {e}")
        return jsonify({'error': str(e)}), 500


@user_keys_bp.route('/km/sync', methods=['POST'])
def force_km_sync():
    """
    Force immediate sync with Next Door KM.
    
    Request Body:
    {
        "users": ["SAE_001", "SAE_002"]  // Optional, sync specific users
    }
    
    Response:
    {
        "success": true,
        "users_synced": 2,
        "keys_received": 800
    }
    """
    try:
        data = request.get_json() or {}
        users = data.get('users')
        
        local_km = get_local_km()
        result = local_km.force_sync(users)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[USER_KEYS_API] force sync error: {e}")
        return jsonify({'error': str(e)}), 500


def register_user_keys_routes(app: flask.Flask):
    """Register the user keys blueprint with the Flask app."""
    app.register_blueprint(user_keys_bp)
    print("[USER_KEYS_API] Routes registered")
