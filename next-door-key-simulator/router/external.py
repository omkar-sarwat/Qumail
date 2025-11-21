import os

import flask
import requests

from keys.key_store import KeyStore
from network.scanner import Scanner
from server import security


# noinspection PyMethodMayBeStatic
class External:
    def __init__(self, scanner: Scanner, key_store: KeyStore):
        self.scanner = scanner
        self.key_store = key_store

    def get_status(self, request: flask.Request, slave_sae_id: str):
        security.ensure_valid_sae_id(request)

        kme = self.scanner.find_kme(slave_sae_id)

        if kme is None:
            return {'message': 'The given slave SAE ID is unknown by this KME.'}, 400

        is_this_sae_slave = slave_sae_id == os.getenv('ATTACHED_SAE_ID')
        master_sae_id = kme[1] if is_this_sae_slave else os.getenv('ATTACHED_SAE_ID')

        # Return sizes in BITS to conform with ETSI QKD-014 reporting
        default_key_size_bytes = int(os.getenv('DEFAULT_KEY_SIZE'))
        max_key_size_bytes = int(os.getenv('MAX_KEY_SIZE'))
        min_key_size_bytes = int(os.getenv('MIN_KEY_SIZE'))

        return {
            'source_KME_ID': kme[0] if is_this_sae_slave else os.getenv('KME_ID'),
            'target_KME_ID': os.getenv('KME_ID') if is_this_sae_slave else kme[0],
            'master_SAE_ID': master_sae_id,
            'slave_SAE_ID': slave_sae_id,
            'key_size': default_key_size_bytes * 8,
            'stored_key_count': len(
                self.key_store.get_keys(master_sae_id, slave_sae_id)
                + self.key_store.get_keys(slave_sae_id, master_sae_id)
            ),
            'max_key_count': int(os.getenv('MAX_KEY_COUNT')),
            'max_key_per_request': int(os.getenv('MAX_KEYS_PER_REQUEST')),
            'max_key_size': max_key_size_bytes * 8,
            'min_key_size': min_key_size_bytes * 8,
            'max_SAE_ID_count': 0
        }

    def get_key(self, request: flask.Request, slave_sae_id: str):
        security.ensure_valid_sae_id(request)

        if request.method == 'POST':
            data = request.get_json()

            # Get data (ETSI QKD-014 uses BITS)
            number_of_keys = data.get('number', 1)
            key_size = data.get('size', int(os.getenv('DEFAULT_KEY_SIZE')) * 8)
            print(f'[ENC_KEYS] Requested key size (bits): {key_size}')
        else:
            # GET request, use default values
            number_of_keys = 1
            key_size = int(os.getenv('DEFAULT_KEY_SIZE'))

        # Validate data
        if number_of_keys > int(os.getenv('MAX_KEYS_PER_REQUEST')):
            return {'message': 'Number of requested keys exceed allowed max keys per request.'}, 400

        # Convert configured limits (stored as bytes in env) to bits for comparison
        max_key_size_bits = int(os.getenv('MAX_KEY_SIZE')) * 8
        min_key_size_bits = int(os.getenv('MIN_KEY_SIZE')) * 8

        if key_size > max_key_size_bits:
            return {'message': 'The requested key size is too large.'}, 400

        if key_size < min_key_size_bits:
            return {'message': 'The requested key size is too small.'}, 400

        # CLOUD MODE: Try scanner first, but fallback to direct mode if SAE not found
        kme = self.scanner.find_kme(slave_sae_id)

        if kme is None:
            # FALLBACK: Direct mode for cloud deployments without SAE discovery
            # This allows enc_keys requests even when scanner hasn't discovered peer SAE
            print(f'[ENC_KEYS] SAE {slave_sae_id} not discovered by scanner - using direct cloud mode')
            master_sae_id = os.getenv('ATTACHED_SAE_ID')
            print(f'[ENC_KEYS] Direct cloud mode: master_sae_id={master_sae_id}, slave_sae_id={slave_sae_id}')
        else:
            is_this_sae_slave = slave_sae_id == os.getenv('ATTACHED_SAE_ID')
            master_sae_id = kme[1] if is_this_sae_slave else os.getenv('ATTACHED_SAE_ID')

        stored_keys = self.key_store.get_keys(master_sae_id, slave_sae_id)

        if len(stored_keys) + number_of_keys > int(os.getenv('MAX_KEY_COUNT')):
            return {'message': 'The requested total of keys exceeds the maximum key count that can be stored.'}, 400

        # Generate keys
        keys = []
        acquire_timeout = float(os.getenv('KEY_ACQUIRE_TIMEOUT', '5'))

        for i in range(number_of_keys):
            # key_size is provided in BITS per ETSI; KeyPool.get_key expects bits as well
            # DON'T remove keys during enc_keys - they'll be removed during dec_keys (OTP consumption)
            key = self.key_store.get_new_key(key_size, timeout=acquire_timeout, remove=False)

            if key is None:
                return {
                    'message': 'Timed out while waiting for quantum keys. Try again shortly.'
                }, 503

            keys.append(key)

        print(f'[ENC_KEYS] Generated {len(keys)} keys for encryption')
        print(f'[ENC_KEYS] Key IDs: {[k["key_ID"] for k in keys]}')
        print(f'[ENC_KEYS] SAE pair: master={master_sae_id}, slave={slave_sae_id}')
        print(f'[ENC_KEYS] Calling append_keys with do_broadcast=True (default)')
        # Log decoded key sizes for debugging (base64 -> bytes length)
        try:
            import base64 as _b64
            decoded_lengths = [_b64.b64decode(k['key']).__len__() for k in keys]
            print(f'[ENC_KEYS] Decoded key sizes (bytes): {decoded_lengths}')
        except Exception:
            print('[ENC_KEYS] Could not decode key sizes for logging')

        self.key_store.append_keys(master_sae_id, slave_sae_id, keys, do_broadcast=True)
        print(f'[ENC_KEYS] append_keys completed, keys should be stored and broadcasted')

        return {'keys': keys}

    def get_key_with_ids(self, request: flask.Request, master_sae_id: str):
        security.ensure_valid_sae_id(request)

        # Get slave_sae_id from client certificate (HTTPS) or header/env (HTTP)
        use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
        
        if use_https:
            # HTTPS mode - get from client certificate
            slave_sae_id = request.environ['client_cert_common_name']
        else:
            # HTTP mode - get from header or use the attached SAE ID
            slave_sae_id = request.headers.get('X-SAE-ID', os.getenv('ATTACHED_SAE_ID', ''))
            print(f"[HTTP MODE] Using slave_sae_id from header/env: {slave_sae_id}")

        # Validate data - but allow empty key_store for cloud mode with shared pool
        has_keys = (
                len(self.key_store.get_keys(master_sae_id, slave_sae_id)) > 0 or
                len(self.key_store.get_keys(slave_sae_id, master_sae_id)) > 0
        )
        
        # For cloud mode: If no keys in key_store, we'll search shared pool later
        # Only return 401 if we're in local mode and no keys exist
        is_cloud_mode = 'onrender.com' in os.getenv('OTHER_KMES', '').lower()
        
        # DISABLED EARLY CHECK: Always proceed to check shared pool
        # if not has_keys and not is_cloud_mode:
        #     return {'message': 'The given master_sae_id is not involved in any key exchanges.'}, 401

        try:
            if request.method == 'POST':
                data = request.get_json()

                # Get data
                requested_keys = list(map(lambda x: x['key_ID'], data['key_IDs']))
                print(f"[DEC_KEYS POST] Requested key IDs: {requested_keys}")
            else:
                # GET request, extract key_ID from query parameters
                # Support both ?key_ID=abc&key_ID=def and ?key_ID=abc,def formats
                key_id_params = request.args.getlist('key_ID')
                print(f"[DEC_KEYS GET] Raw key_ID params: {key_id_params}")
                
                if len(key_id_params) == 0:
                    # No key_ID specified, return all available keys
                    all_keys = self.key_store.get_keys(master_sae_id, slave_sae_id)
                    requested_keys = [k['key_ID'] for k in all_keys]
                    print(f"[DEC_KEYS GET] No key_ID specified, returning all keys: {requested_keys}")
                else:
                    # Flatten list in case of comma-separated values
                    requested_keys = []
                    for param in key_id_params:
                        requested_keys.extend(param.split(','))
                    print(f"[DEC_KEYS GET] Parsed key IDs: {requested_keys}")

            # Try both directions: master->slave and slave->master
            # This handles cases where keys were stored in different direction
            keys_master_to_slave = self.key_store.get_keys(master_sae_id, slave_sae_id)
            keys_slave_to_master = self.key_store.get_keys(slave_sae_id, master_sae_id)
            all_available_keys = keys_master_to_slave + keys_slave_to_master
            
            print(f"[DEC_KEYS] Available keys in KeyStore (master->slave): {len(keys_master_to_slave)}")
            print(f"[DEC_KEYS] Available keys in KeyStore (slave->master): {len(keys_slave_to_master)}")
            
            # Filter for requested keys found in KeyStore
            selected_keys = list(filter(
                lambda x: x['key_ID'] in requested_keys,
                all_available_keys
            ))
            
            # Check which keys are missing
            found_ids = [k['key_ID'] for k in selected_keys]
            missing_ids = [kid for kid in requested_keys if kid not in found_ids]
            
            if len(missing_ids) > 0:
                print(f"[DEC_KEYS] {len(missing_ids)} keys missing from KeyStore, checking Shared Pool...")
                try:
                    kme_id = os.getenv('KME_ID', '1')
                    for key_id in missing_ids:
                        # Use key_store's key_pool (the CLIENT) instead of pool_server directly
                        # The CLIENT handles cross-KME fetching automatically
                        try:
                            # Check if key_pool has get_key_by_id method (SharedKeyPoolClient)
                            if hasattr(self.key_store.key_pool, 'get_key_by_id'):
                                key = self.key_store.key_pool.get_key_by_id(key_id)
                                if key:
                                    print(f"[DEC_KEYS] Found missing key {key_id[:16]}... via key_pool CLIENT")
                                    selected_keys.append(key)
                                else:
                                    print(f"[DEC_KEYS] Key {key_id[:16]}... not found via key_pool")
                            else:
                                print(f"[DEC_KEYS] WARNING: key_pool does not have get_key_by_id method")
                                # Fallback: direct HTTP call to KME1 if we're on KME2
                                if kme_id == '2':
                                    kme1_url = os.getenv('OTHER_KMES', 'http://127.0.0.1:8010')
                                    print(f"[DEC_KEYS] KME2: Fetching from KME1 via HTTP: {kme1_url}")
                                    resp = requests.post(
                                        f"{kme1_url}/api/v1/internal/get_reserved_key",
                                        json={"key_id": key_id, "kme_id": "2", "remove": True},
                                        timeout=10,
                                        verify=False
                                    )
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        if 'key' in data:
                                            print(f"[DEC_KEYS] KME2: Got key via direct HTTP")
                                            selected_keys.append(data['key'])
                                        else:
                                            print(f"[DEC_KEYS] KME2: Key not in response")
                                    else:
                                        print(f"[DEC_KEYS] KME2: HTTP error {resp.status_code}")
                        except Exception as e:
                            print(f"[DEC_KEYS ERROR] Exception getting key {key_id[:16]}...: {e}")
                            import traceback
                            traceback.print_exc()

                except Exception as e:
                    print(f"[DEC_KEYS ERROR] Failed to check shared pool: {e}")
            
            print(f"[DEC_KEYS] Final selected keys: {len(selected_keys)}")
        except IndexError as e:
            print(f"[DEC_KEYS ERROR] IndexError: {e}")
            return {'message': 'The given data is in invalid format.'}, 400
        except Exception as e:
            print(f"[DEC_KEYS ERROR] Unexpected error: {e}")
            return {'message': f'Error processing request: {str(e)}'}, 400

        if len(selected_keys) == 0:
            print(f"[DEC_KEYS ERROR] None of the requested keys found. Returning 404.")
            # Log available key IDs for debugging
            available_ids = [k['key_ID'] for k in all_available_keys]
            print(f"[DEC_KEYS DEBUG] Requested: {requested_keys}")
            print(f"[DEC_KEYS DEBUG] Available in pool ({len(available_ids)}): {available_ids[:10]}... (first 10)")
            if len(available_ids) > 0:
                print(f"[DEC_KEYS DEBUG] Last available: {available_ids[-1]}")
            
            return {'message': 'None of the requested keys exist in this KME.'}, 404
        if len(requested_keys) != len(selected_keys):
            print(f"[DEC_KEYS WARNING] Requested {len(requested_keys)} keys but only found {len(selected_keys)}. Returning partial result.")
            # Return partial result with found keys, but indicate missing keys
            return {'message': 'Some requested keys missing, returning available keys.', 'keys': selected_keys}, 206

        # OTP CONSUMPTION: Remove keys from KeyStore after successful retrieval (true one-time use)
        print(f"[DEC_KEYS] Removing {len(selected_keys)} keys from KeyStore (OTP consumption)")
        self.key_store.remove_keys(master_sae_id, slave_sae_id, selected_keys, do_broadcast=True)
        
        # Note: Keys are automatically removed from SharedPool during get_key_by_id with remove=True
        # No need for additional cleanup here
        
        print(f"[DEC_KEYS] Returning {len(selected_keys)} keys (now consumed/removed)")
        return {'keys': selected_keys}

    def mark_consumed(self, request: flask.Request):
        """
        Mark a key as consumed (permanently remove from shared pool)
        Used after successful decryption and caching
        """
        try:
            data = request.get_json()
            key_id = data.get('key_id')
            
            if not key_id:
                return {'message': 'Missing key_id'}, 400
                
            print(f"[MARK_CONSUMED] Request to consume key: {key_id}")
            
            # Try to remove from shared pool
            # Check if we are in cloud mode or local mode
            is_cloud_mode = 'onrender.com' in os.getenv('OTHER_KMES', '').lower()
            
            # ALWAYS try to remove from shared pool (works for both cloud and local shared pool)
            try:
                from keys.shared_key_pool import get_shared_pool_server
                pool = get_shared_pool_server()
                kme_id = os.getenv('KME_ID', '1')
                
                # remove=True will delete it permanently
                key = pool.get_key_by_id(key_id, kme_id, remove=True)
                
                if key:
                    print(f"[MARK_CONSUMED] Successfully removed key {key_id} from pool")
                    return {'message': 'Key consumed', 'key_id': key_id}, 200
                else:
                    print(f"[MARK_CONSUMED] Key {key_id} not found in pool (already consumed?)")
                    return {'message': 'Key not found or already consumed'}, 404
            except Exception as e:
                print(f"[MARK_CONSUMED ERROR] Shared pool error: {e}")
                return {'message': f'Shared pool error: {str(e)}'}, 500
                
        except Exception as e:
            print(f"[MARK_CONSUMED ERROR] Unexpected error: {e}")
            return {'message': f'Error processing request: {str(e)}'}, 500
