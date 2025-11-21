#!/usr/bin/env python3
"""QuMail Render deployment smoke test."""

import argparse
import sys
import textwrap
from typing import Tuple

import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import redis


def check_http_endpoint(name: str, url: str) -> Tuple[bool, str]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return True, f"{name} OK ({response.status_code})"
    except Exception as exc:  # noqa: BLE001
        return False, f"{name} FAILED: {exc}"


def check_kme_key_pool(url: str) -> Tuple[bool, str]:
    endpoint = url.rstrip('/') + '/api/v1/kme/key-pool'
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        payload = response.json()
        available = payload.get('pool_status', {}).get('available_keys')
        preview = len(payload.get('preview_keys', []))
        if available is None:
            return True, f"Key pool reachable; preview={preview}"
        return (available > 0, f"Key pool available={available} preview={preview}")
    except Exception as exc:  # noqa: BLE001
        return False, f"Key pool check failed: {exc}"


def check_mongo(uri: str) -> Tuple[bool, str]:
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return True, "MongoDB ping OK"
    except PyMongoError as exc:
        return False, f"MongoDB connection failed: {exc}"


def check_redis(url: str) -> Tuple[bool, str]:
    try:
        client = redis.Redis.from_url(url)
        client.ping()
        return True, "Redis ping OK"
    except Exception as exc:  # noqa: BLE001
        return False, f"Redis connection failed: {exc}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Render deployment endpoints",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=textwrap.dedent(
            """Example:
                python scripts/check_render_deployment.py \\
                  --backend https://qumail-backend.onrender.com \\
                  --kme1 https://qumail-kme1.onrender.com \\
                  --kme2 https://qumail-kme2.onrender.com \\
                  --mongo "mongodb+srv://user:pass@cluster0.mongodb.net/qumail" \\
                  --redis "redis://default:pass@redis-xxxxx.cloud.redislabs.com:12345"
            """
        ),
    )
    parser.add_argument('--backend', required=True, help='Backend base URL')
    parser.add_argument('--kme1', required=True, help='KME1 base URL')
    parser.add_argument('--kme2', required=True, help='KME2 base URL')
    parser.add_argument('--mongo', required=True, help='MongoDB Atlas URI')
    parser.add_argument('--redis', required=True, help='Redis connection URL')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = []

    checks.append(check_http_endpoint('Backend /health', args.backend.rstrip('/') + '/health'))
    checks.append(check_http_endpoint('Backend /api/v1/health', args.backend.rstrip('/') + '/api/v1/health'))

    checks.append(check_http_endpoint('KME1 status', args.kme1.rstrip('/') + '/api/v1/kme/status'))
    checks.append(check_http_endpoint('KME2 status', args.kme2.rstrip('/') + '/api/v1/kme/status'))
    checks.append(check_kme_key_pool(args.kme1))
    checks.append(check_kme_key_pool(args.kme2))

    checks.append(check_mongo(args.mongo))
    checks.append(check_redis(args.redis))

    all_ok = True
    print('=== QuMail Cloud Deployment Verification ===')
    for success, message in checks:
        status = '✅' if success else '❌'
        print(f"{status} {message}")
        all_ok &= success

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
