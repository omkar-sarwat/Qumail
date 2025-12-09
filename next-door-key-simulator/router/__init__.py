"""
Router module for Next Door Key Simulator.

Contains ETSI GS QKD 014 compliant REST API routes.
"""
from router.user_keys import user_keys_bp, register_user_keys_routes

__all__ = [
    'user_keys_bp',
    'register_user_keys_routes'
]
