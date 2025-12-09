"""
Module for initializing global instances of optimized KM clients for Next Door Key Simulator
Updated for ETSI GS QKD 014 V1.1.1 compliance with proper SSL/TLS security
"""

from .optimized_km_client import OptimizedKMClient
from pathlib import Path
import os

# Global clients
_km1_client = None
_km2_client = None

def create_optimized_km_clients():
    """Create optimized KM clients for QuMail-KMS with SSL/TLS or HTTP"""
    
    # Get URLs from environment variables - Use Render cloud KME servers
    km1_base_url = os.getenv("KM1_BASE_URL", "https://qumail-kme1-pmsy.onrender.com")
    km2_base_url = os.getenv("KM2_BASE_URL", "https://qumail-kme2-pmsy.onrender.com")
    
    # Base directory for the project
    base_dir = Path(__file__).parent.parent.parent.parent
    cert_dir = base_dir / "next-door-key-simulator" / "certs"
    
    # Check if we're using cloud KME servers (Render.com) - they don't use client certificates
    is_cloud_kme = "onrender.com" in km1_base_url.lower() or "onrender.com" in km2_base_url.lower()
    
    if is_cloud_kme:
        # Cloud KME servers (Render.com) - no client certificates needed
        km1_client = OptimizedKMClient(
            base_url=km1_base_url,
            sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
            client_cert_path=None,
            client_key_path=None,
            ca_cert_path=None
        )
        
        km2_client = OptimizedKMClient(
            base_url=km2_base_url,
            sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            client_cert_path=None,
            client_key_path=None,
            ca_cert_path=None
        )
    else:
        # Local KME servers - use certificates for mutual TLS
        km1_client = OptimizedKMClient(
            base_url=km1_base_url,
            sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
            client_cert_path=str(cert_dir / "sae-1.crt.pem"),
            client_key_path=str(cert_dir / "sae-1.key.pem"),
            ca_cert_path=str(cert_dir / "ca.crt.pem")
        )
        
        km2_client = OptimizedKMClient(
            base_url=km2_base_url,
            sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            client_cert_path=str(cert_dir / "sae-2.crt.pem"),
            client_key_path=str(cert_dir / "sae-2.key.pem"),
            ca_cert_path=str(cert_dir / "ca.crt.pem")
        )
    
    return km1_client, km2_client

def use_optimized_km_clients():
    """
    Replace global km_client instances with optimized versions for Next Door Key Simulator
    This should be called at application startup
    
    Returns:
        Tuple of (km1_client, km2_client)
    """
    global _km1_client, _km2_client
    
    # Create new optimized KM clients
    km1, km2 = create_optimized_km_clients()
    
    # Store them in module-level variables
    _km1_client = km1
    _km2_client = km2
    
    # Also update the original km_client module for backward compatibility
    try:
        from . import km_client
        km_client.km1_client = km1
        km_client.km2_client = km2
    except ImportError:
        pass  # Optional dependency
    
    return km1, km2

def get_optimized_km_clients():
    """
    Get the optimized KM clients for Next Door Key Simulator.
    If they haven't been initialized yet, initialize them with default values.
    
    Returns:
        Tuple of (km1_client, km2_client)
    """
    global _km1_client, _km2_client
    
    if _km1_client is None or _km2_client is None:
        return use_optimized_km_clients()
    
    return _km1_client, _km2_client
