import json
import os
from urllib.parse import urlparse

import requests


class Broadcaster:
    def __init__(self):
        self.other_kmes = [k.strip() for k in os.getenv('OTHER_KMES', '').split(',') if k.strip()]
        self.certs = (os.getenv('KME_CERT'), os.getenv('KME_KEY'))
        self.timeout = float(os.getenv('NETWORK_TIMEOUT', '5'))

        scheme = 'https' if os.getenv('USE_HTTPS', 'true').lower() == 'true' else 'http'
        self_origin = f"{scheme}://{os.getenv('HOST')}:{os.getenv('PORT')}"
        self.self_netloc = urlparse(self_origin).netloc

    def send_keys(self, master_sae_id: str, slave_sae_id: str, keys: list) -> None:
        self.__broadcast('/api/v1/kme/keys/exchange', {
            'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys
        })

    def remove_keys(self, master_sae_id: str, slave_sae_id: str, keys: list) -> None:
        self.__broadcast('/api/v1/kme/keys/remove', {
            'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys
        })

    def __broadcast(self, url: str, data: dict) -> None:
        if not self.other_kmes:
            return

        data = json.loads(json.dumps(data, default=str))

        for kme in self.other_kmes:
            parsed = urlparse(kme)
            if not parsed.scheme or not parsed.netloc:
                print(f'WARNING: Skipping invalid KME endpoint "{kme}" during broadcast')
                continue

            if parsed.netloc == self.self_netloc:
                continue

            print(f'[BROADCAST] Attempting to POST to {kme}{url}')
            print(f'[BROADCAST] Payload: {json.dumps(data)}')
            try:
                # Only use client certs if USE_HTTPS is true AND certs exist
                use_https = os.getenv('USE_HTTPS', 'true').lower() == 'true'
                cert_param = None
                
                if use_https and parsed.scheme == 'https':
                    # Check if cert files exist before using them
                    cert_path, key_path = self.certs
                    if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
                        cert_param = self.certs
                    else:
                        print(f'[BROADCAST] Certificate files not found, proceeding without client cert')
                
                response = requests.post(
                    f'{kme}{url}',
                    verify=False,  # Always disable server cert verification for testing
                    cert=cert_param,
                    json=data,
                    timeout=self.timeout
                )
                print(f'[BROADCAST] Response status: {response.status_code}')
                print(f'[BROADCAST] Response body: {response.text}')
            except requests.exceptions.RequestException as exc:
                print(f'WARNING: Failed to broadcast keys to {kme}{url}: {exc}')
