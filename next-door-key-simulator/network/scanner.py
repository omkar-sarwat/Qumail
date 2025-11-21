import os
import threading

import requests


class Scanner:
    def __init__(self, kme_list: list, kme_lock: threading.Lock):
        self.kme_list = kme_list
        self.kme_lock = kme_lock
        self.stop = threading.Event()
        # Reduced timeout for faster failure detection
        self.timeout = float(os.getenv('NETWORK_TIMEOUT', '10.0'))
        self.scan_interval = 60  # seconds between scans

    def start(self) -> None:
        # Delay initial scan to let server start first
        self.stop.wait(5)  # Wait 5 seconds before first scan
        
        # Perform initial scan once at startup
        if not self.stop.is_set():
            self._do_scan()
        
        # Then run periodic scans with longer intervals to reduce overhead
        while not self.stop.is_set():
            self.stop.wait(self.scan_interval)
            if not self.stop.is_set():
                self._do_scan()
    
    def _do_scan(self) -> None:
        """Perform a single KME scan - non-blocking with proper lock usage"""
        # Use try-finally to ensure lock is always released
        acquired = self.kme_lock.acquire(blocking=False)
        if not acquired:
            # If lock is busy, skip this scan cycle
            print('[SCANNER] Skipping scan - system busy')
            return
        
        try:
            old_kme_list = list(map(lambda x: x['KME_ID'], self.kme_list))

            self.kme_list.clear()

            for kme in os.getenv('OTHER_KMES', '').split(','):
                if not kme.strip():
                    continue
                    
                try:
                    use_https = os.getenv('USE_HTTPS', 'true').lower() == 'true'

                    if use_https and kme.startswith('https://'):
                        data = requests.get(
                            url=f'{kme}/api/v1/kme/status',
                            verify=False,
                            cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
                            timeout=self.timeout
                        ).json()
                    else:
                        data = requests.get(
                            url=f'{kme}/api/v1/kme/status',
                            timeout=self.timeout
                        ).json()

                    self.kme_list.append(data)
                except requests.exceptions.Timeout:
                    print(f'[SCANNER] KME {kme} timed out after {self.timeout}s')
                except requests.exceptions.ConnectionError as exception:
                    print(f'[SCANNER] Unable to connect to {kme}: {exception}')
                except requests.exceptions.RequestException as exception:
                    print(f'[SCANNER] Unable to fetch KME status for {kme}: {exception}')
                except requests.exceptions.JSONDecodeError:
                    print(f'[SCANNER] KME {kme} did not return valid JSON response.')
                except Exception as e:
                    print(f'[SCANNER] Unexpected error scanning {kme}: {e}')

            new_kme_list = set(list(map(lambda x: x['KME_ID'], self.kme_list)) + old_kme_list)

            if len(self.kme_list) == 0 and len(old_kme_list) > 0:
                print('[SCANNER] Warning: Lost all KMEs from domain (may be temporary)')
            elif len(self.kme_list) != 0 and len(new_kme_list) != len(old_kme_list):
                print('[SCANNER] Refreshed KME statuses, established new domain of KMEs:')
                print(self.kme_list)
                
        finally:
            self.kme_lock.release()

    def find_kme(self, sae_id: str) -> tuple[str, str] | None:
        # First check if this is our own SAE
        if os.getenv('ATTACHED_SAE_ID') == sae_id:
            return os.getenv('KME_ID'), os.getenv('ATTACHED_SAE_ID')

        # Then check discovered KMEs
        self.kme_lock.acquire(blocking=True)
        try:
            for value in self.kme_list:
                if value.get('SAE_ID') == sae_id:
                    return value.get('KME_ID'), value.get('SAE_ID')
        finally:
            self.kme_lock.release()

        # If not found, log the issue for debugging
        print(f'[SCANNER] SAE ID {sae_id} not found in discovered KMEs: {[k.get("SAE_ID") for k in self.kme_list]}')
        return None
