import os

import OpenSSL
import flask
from flask import Request


def ensure_valid_sae_id(request: Request):
    # Check if we're running in HTTPS mode or HTTP mode
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    
    if use_https:
        # HTTPS mode - perform SSL certificate validation
        sae_id = request.environ.get('client_cert_common_name')
        
        if not sae_id:
            print('No client certificate provided in HTTPS mode!')
            flask.abort(401)
            
        if sae_id != os.getenv('ATTACHED_SAE_ID'):
            print('Client cert common name does not match the attached_sae_id value!')
            flask.abort(401)

        sae_x509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM,
            open(os.getenv('SAE_CERT'), 'rb').read()
        )

        if sae_x509.get_serial_number() != request.environ.get('client_cert_serial_number'):
            print('Client cert serial number does not match the loaded SAE certificate serial number!')
            flask.abort(401)
    else:
        # HTTP mode - skip certificate validation for testing
        print(f'HTTP mode: Skipping certificate validation for testing purposes')
        pass
