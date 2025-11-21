import flask
import urllib3
import os
from dotenv import load_dotenv
from flask import Flask, request
from markupsafe import escape

from server.app import App

# Don't clear environment variables - Render needs them!
# Only clear if we're loading from .env files and they conflict

# Load base env first (don't override Render's environment variables)
load_dotenv('.env', override=False)

# Then load the appropriate KME configuration file based on KME_ID
kme_id = os.getenv('KME_ID', '1')
print(f"Loading configuration for KME_ID: {kme_id}")  # Debug

if kme_id == '1':
    # Don't override environment variables set by Render
    load_dotenv('.env.kme1', override=False)
    print(f"Loaded .env.kme1 - HOST: {os.getenv('HOST')} - OTHER_KMES: {os.getenv('OTHER_KMES')}")  # Debug
elif kme_id == '2':
    # Don't override environment variables set by Render
    load_dotenv('.env.kme2', override=False)
    print(f"Loaded .env.kme2 - HOST: {os.getenv('HOST')} - OTHER_KMES: {os.getenv('OTHER_KMES')}")  # Debug

instance = Flask(__name__)
app = App(instance)


def main():
    # Disable unsecure HTTPS warnings (e.g. invalid certificate)
    urllib3.disable_warnings()

    try:
        app.start()
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


@instance.before_request
def before_request():
    app.before_request()


@instance.after_request
def after_request(response: flask.Response):
    return app.after_request(response)


@instance.route('/api/v1/kme/status')
def get_kme_status():
    return app.internal_routes.get_kme_status()


@instance.route('/api/v1/kme/key-pool')
def get_key_pool():
    return app.internal_routes.get_key_pool()


@instance.route('/api/v1/internal/get_shared_key', methods=['POST'])
def get_shared_key():
    return app.internal_routes.get_shared_key(request)


@instance.route('/api/v1/internal/get_reserved_key', methods=['POST'])
def get_reserved_key():
    return app.internal_routes.get_reserved_key_by_id(request)


@instance.route('/api/v1/kme/keys/exchange', methods=['POST'])
def key_exchange():
    return app.internal_routes.do_kme_key_exchange(request)


@instance.route('/api/v1/kme/keys/remove', methods=['POST'])
def key_remove_exchange():
    return app.internal_routes.do_remove_kme_key(request)


@instance.route('/api/v1/keys/<slave_sae_id>/status')
def get_status(slave_sae_id):
    return app.external_routes.get_status(request, escape(slave_sae_id))


@instance.route('/api/v1/keys/<slave_sae_id>/enc_keys', methods=['POST','GET'])
def get_key(slave_sae_id):
    return app.external_routes.get_key(request, escape(slave_sae_id))


@instance.route('/api/v1/keys/<master_sae_id>/dec_keys', methods=['POST','GET'])
def get_key_with_ids(master_sae_id):
    return app.external_routes.get_key_with_ids(request, escape(master_sae_id))


@instance.route('/api/v1/keys/mark_consumed', methods=['POST'])
def mark_consumed():
    return app.external_routes.mark_consumed(request)


if __name__ == '__main__':
    main()
