import os
import requests

import flask

from keys.key_store import KeyStore
from keys.shared_key_pool import get_shared_pool_server


# noinspection PyMethodMayBeStatic
class Internal:
    def __init__(self, key_store: KeyStore):
        self.key_store = key_store

    def get_kme_status(self):
        """Get KME status including shared pool statistics"""
        kme_id = os.getenv('KME_ID', '1')
        
        # KME2: Fetch pool status from KME1
        if kme_id == '2':
            try:
                kme1_url = os.getenv('OTHER_KMES', 'http://127.0.0.1:8010')
                response = requests.get(
                    f"{kme1_url}/api/v1/kme/status",
                    timeout=5,
                    verify=False
                )
                if response.status_code == 200:
                    kme1_data = response.json()
                    pool_status = kme1_data.get('shared_pool', {})
                else:
                    pool_status = {"error": "Failed to fetch from KME1"}
            except Exception as e:
                pool_status = {"error": str(e)}
        else:
            # KME1: Get local pool status
            try:
                pool_server = get_shared_pool_server()
                pool_status = pool_server.get_status()
            except Exception as e:
                pool_status = {"error": str(e)}
        
        return {
            'KME_ID': kme_id,
            'SAE_ID': os.getenv('ATTACHED_SAE_ID'),
            'role': 'MASTER (Generator)' if kme_id == '1' else 'SLAVE (Consumer)',
            'shared_pool': pool_status
        }
    
    def get_shared_key(self, request: flask.Request):
        """
        Internal endpoint for KME2 to fetch keys from KME1's shared pool
        Only KME1 should respond to this endpoint
        """
        kme_id = os.getenv('KME_ID', '1')
        
        if kme_id != '1':
            return {'error': 'This endpoint is only available on KME1'}, 403
        
        try:
            data = request.get_json()
            requesting_kme = data.get('kme_id', '2')
            count = data.get('count', 1)
            timeout = data.get('timeout', 10.0)
            
            # Get keys from pool
            pool_server = get_shared_pool_server()
            keys = pool_server.get_keys(count, requesting_kme, timeout)
            
            return {
                'keys': keys,
                'count': len(keys),
                'kme_id': requesting_kme
            }
        except Exception as e:
            return {'error': str(e)}, 500
    
    def get_reserved_key_by_id(self, request: flask.Request):
        """
        Internal endpoint for KME2 to retrieve reserved keys by ID from KME1
        Reserved keys are those used for encryption but not yet consumed by decryption
        Only KME1 should respond to this endpoint
        """
        kme_id = os.getenv('KME_ID', '1')
        
        if kme_id != '1':
            return {'error': 'This endpoint is only available on KME1'}, 403
        
        try:
            data = request.get_json()
            key_id = data.get('key_id')
            requesting_kme = data.get('kme_id', '2')
            remove = data.get('remove', True)  # Default to True for OTP consumption
            
            if not key_id:
                return {'error': 'key_id is required'}, 400
            
            # Get key from shared pool (checks reserved_keys first)
            pool_server = get_shared_pool_server()
            key = pool_server.get_key_by_id(key_id, requesting_kme, remove=remove)
            
            if key:
                print(f"[INTERNAL] Served reserved key {key_id[:16]}... to KME{requesting_kme}, remove={remove}")
                return {
                    'key': key,
                    'key_id': key_id,
                    'consumed': remove
                }
            else:
                print(f"[INTERNAL] Reserved key {key_id[:16]}... not found for KME{requesting_kme}")
                return {'error': f'Key {key_id} not found in reserved keys or pool'}, 404
                
        except Exception as e:
            print(f"[INTERNAL ERROR] Failed to retrieve reserved key: {e}")
            return {'error': str(e)}, 500

    def get_key_pool(self):
        """Get key pool contents"""
        kme_id = os.getenv('KME_ID', '1')
        
        # Get shared pool status
        try:
            pool_server = get_shared_pool_server()
            pool_status = pool_server.get_status()
            
            # Return pool keys (first 10 for preview)
            with pool_server.condition:
                preview_keys = pool_server.keys[:10]
            
            return {
                'kme_id': kme_id,
                'role': 'MASTER (Generator)' if kme_id == '1' else 'SLAVE (Consumer)',
                'pool_status': pool_status,
                'preview_keys': preview_keys,
                'note': 'Showing first 10 keys from shared pool'
            }
        except Exception as e:
            return {'error': str(e)}

    def do_kme_key_exchange(self, request: flask.Request):
        data = request.get_json()

        return self.key_store.append_keys(
            data['master_sae_id'],
            data['slave_sae_id'],
            data['keys'],
            do_broadcast=False)

    def do_remove_kme_key(self, request: flask.Request):
        data = request.get_json()

        self.key_store.remove_keys(
            data['master_sae_id'],
            data['slave_sae_id'],
            data['keys'],
            do_broadcast=False)

        return {'message': 'Keys have been removed from the local key store.'}
