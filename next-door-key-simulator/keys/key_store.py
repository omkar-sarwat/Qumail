from typing import Optional, Dict
from keys.key_pool import KeyPool
from network.broadcaster import Broadcaster


# noinspection PyMethodMayBeStatic
class KeyStore:
    def __init__(self, key_pool: KeyPool, broadcaster: Broadcaster):
        self.container: list[dict[str, object]] = []
        self.key_pool = key_pool
        self.broadcaster = broadcaster

    def get_sae_key_container(self, master_sae_id: str, slave_sae_id) -> list:
        return list(filter(
            lambda x: x['master_sae_id'] == master_sae_id and x['slave_sae_id'] == slave_sae_id,
            self.container
        ))

    def get_new_key(self, key_size: int, timeout: Optional[float] = None, remove: bool = False) -> Optional[Dict[str, str]]:
        """Get a new key from the pool.
        
        Args:
            key_size: Key size in bits
            timeout: Timeout in seconds
            remove: If True, remove from pool (OTP consumption). If False, copy only (for enc_keys).
        """
        return self.key_pool.get_key(key_size, timeout=timeout, remove=remove)

    def get_keys(self, master_sae_id: str, slave_sae_id: str) -> list:
        container = self.get_sae_key_container(master_sae_id, slave_sae_id)

        return [] if len(container) == 0 else container[0]['keys']

    def append_keys(self, master_sae_id: str, slave_sae_id: str, keys: list, do_broadcast: bool = True) -> list:
        container = self.get_sae_key_container(master_sae_id, slave_sae_id)

        if len(container) == 0:
            self.container.append({'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys})
        else:
            # FIXED: APPEND new keys instead of replacing old keys
            # This allows different security levels to coexist in shared pool
            for existing_container in self.container:
                if (existing_container['master_sae_id'] == master_sae_id and 
                    existing_container['slave_sae_id'] == slave_sae_id):
                    existing_container['keys'].extend(keys)
                    break

        print(f'[KEY_STORE] append_keys called: master_sae_id={master_sae_id}, slave_sae_id={slave_sae_id}, keys={[k["key_ID"] for k in keys]}, do_broadcast={do_broadcast}')
        if do_broadcast:
            print(f'[KEY_STORE] Broadcasting keys to other KMEs (non-blocking)...')
            try:
                self.broadcaster.send_keys(master_sae_id, slave_sae_id, keys)
            except Exception as e:
                # Don't fail the request if broadcast fails - just log it
                print(f'[KEY_STORE] WARNING: Broadcast failed (non-critical): {e}')

        return keys

    def remove_keys(self, master_sae_id: str, slave_sae_id: str, keys: list, do_broadcast: bool = True):
        print(f'[KEY_STORE] remove_keys called: master_sae_id={master_sae_id}, slave_sae_id={slave_sae_id}, keys={[k["key_ID"] for k in keys]}, do_broadcast={do_broadcast}')
        print(f'[KEY_STORE] Before removal: {self._container_state()}')
        for key in keys:
            for i, value in enumerate(self.container):
                if value['master_sae_id'] == master_sae_id and value['slave_sae_id'] == slave_sae_id:
                    for j, k in enumerate(value['keys']):
                        if k['key_ID'] == key['key_ID']:
                            print(f'[KEY_STORE] Removing key_ID={k["key_ID"]} from ({master_sae_id}, {slave_sae_id})')
                            del self.container[i]['keys'][j]
                            break
                    if len(self.container[i]['keys']) == 0:
                        print(f'[KEY_STORE] All keys removed for ({master_sae_id}, {slave_sae_id}), deleting container entry')
                        del self.container[i]
                        break
        print(f'[KEY_STORE] After removal: {self._container_state()}')
        if do_broadcast:
            print(f'[KEY_STORE] Broadcasting key removal to other KMEs...')
            self.broadcaster.remove_keys(master_sae_id, slave_sae_id, keys)

    def _container_state(self):
        return [(entry['master_sae_id'], entry['slave_sae_id'], [k['key_ID'] for k in entry['keys']]) for entry in self.container]
