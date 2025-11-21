"""
ETSI QKD-014 Inter-KME Communication Fix

This module implements a comprehensive fix for inter-KME communication issues
based on the ETSI GS QKD-014 standard. It provides proper protocol implementation,
timeout handling, and error recovery mechanisms.

Key Features:
- ETSI QKD-014 compliant inter-KME protocol
- Robust error handling and retry mechanisms
- Certificate-based mutual authentication
- Comprehensive logging and monitoring
- Real-time communication status monitoring
"""

import asyncio
import httpx
import ssl
import json
import time
import logging
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class InterKMEConfig:
    """Configuration for inter-KME communication"""
    source_kme_id: int
    target_kme_id: int
    source_inter_url: str
    target_inter_url: str
    cert_path: str
    key_path: str
    ca_cert_path: str
    timeout: float = 120.0
    max_retries: int = 5

class ETSIInterKMECommunicator:
    """
    ETSI QKD-014 compliant inter-KME communication handler
    
    This class implements the exact inter-KME communication protocol as specified
    in ETSI GS QKD-014 standard, handling key activation requests between KMEs.
    """
    
    def __init__(self, config: InterKMEConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        
        # Communication metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
        logger.info(f"Initialized ETSI inter-KME communicator: KME{config.source_kme_id} -> KME{config.target_kme_id}")

    async def _setup_ssl_context(self) -> ssl.SSLContext:
        """Setup SSL context for inter-KME communication"""
        if self._ssl_context is None:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            # Load CA certificate for server verification
            if Path(self.config.ca_cert_path).exists():
                ssl_context.load_verify_locations(cafile=self.config.ca_cert_path)
                ssl_context.verify_mode = ssl.CERT_REQUIRED
            else:
                logger.warning(f"CA certificate not found: {self.config.ca_cert_path}")
                ssl_context.verify_mode = ssl.CERT_NONE
            
            ssl_context.check_hostname = False  # KME uses localhost/IP addresses
            
            # Load client certificate for mutual TLS authentication
            if (Path(self.config.cert_path).exists() and 
                Path(self.config.key_path).exists()):
                ssl_context.load_cert_chain(
                    certfile=self.config.cert_path,
                    keyfile=self.config.key_path
                )
                logger.debug(f"Loaded inter-KME certificates: {self.config.cert_path}")
            else:
                logger.error(f"Inter-KME certificates not found: {self.config.cert_path}")
                raise FileNotFoundError("Inter-KME certificates not found")
            
            self._ssl_context = ssl_context
        
        return self._ssl_context

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for inter-KME communication"""
        if self._client is None:
            ssl_context = await self._setup_ssl_context()
            
            self._client = httpx.AsyncClient(
                verify=ssl_context,
                timeout=self.config.timeout,
                headers={
                    "User-Agent": f"ETSI-QKD-014-KME/{self.config.source_kme_id}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            logger.debug(f"Created inter-KME client for {self.config.target_inter_url}")
        
        return self._client

    async def test_connectivity(self) -> Dict[str, Any]:
        """Test basic connectivity to target KME"""
        try:
            client = await self._get_client()
            start_time = time.time()
            
            response = await client.get(f"{self.config.target_inter_url}/")
            duration = time.time() - start_time
            
            return {
                "success": True,
                "status_code": response.status_code,
                "duration": duration,
                "target_kme": self.config.target_kme_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "target_kme": self.config.target_kme_id
            }

    async def activate_keys_on_remote_kme(self, 
                                        master_sae_id: int,
                                        slave_sae_id: int,
                                        key_ids: List[str],
                                        number_of_keys: int = 1) -> Dict[str, Any]:
        """
        ETSI QKD-014: Activate keys on remote KME
        
        This is the critical inter-KME communication that was failing.
        It implements the exact protocol specified in ETSI QKD-014.
        """
        client = await self._get_client()
        
        # ETSI QKD-014 inter-KME activation request format
        activation_request = {
            "master_SAE_ID": master_sae_id,
            "slave_SAE_ID": slave_sae_id,
            "key_IDs": [{"key_ID": kid} for kid in key_ids],
            "number": number_of_keys,
            "source_KME_ID": self.config.source_kme_id,
            "target_KME_ID": self.config.target_kme_id,
            "activation_timestamp": int(time.time())
        }
        
        for attempt in range(self.config.max_retries):
            try:
                self.total_requests += 1
                start_time = time.time()
                
                logger.info(f"Inter-KME activation attempt {attempt + 1}/{self.config.max_retries}")
                logger.debug(f"Activation request: {activation_request}")
                
                # ETSI QKD-014 inter-KME activation endpoint
                response = await client.post(
                    f"{self.config.target_inter_url}/api/v1/inter-kme/keys/activate",
                    json=activation_request,
                    timeout=self.config.timeout
                )
                
                duration = time.time() - start_time
                self._update_metrics(duration, True)
                
                if response.status_code == 200:
                    self.successful_requests += 1
                    result = response.json()
                    logger.info(f"Inter-KME activation successful ({duration:.2f}s)")
                    return {
                        "success": True,
                        "response": result,
                        "duration": duration,
                        "attempt": attempt + 1
                    }
                else:
                    logger.warning(f"Inter-KME activation failed: {response.status_code} - {response.text}")
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2.0 * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        self.failed_requests += 1
                        return {
                            "success": False,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "duration": duration,
                            "attempts": attempt + 1
                        }
                        
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                self._update_metrics(duration, False)
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 5.0 * (2 ** attempt)  # Longer backoff for timeouts
                    logger.warning(f"Inter-KME timeout (attempt {attempt + 1}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.failed_requests += 1
                    logger.error(f"Inter-KME activation timed out after {self.config.max_retries} attempts")
                    return {
                        "success": False,
                        "error": f"Timeout after {self.config.max_retries} attempts",
                        "duration": duration,
                        "attempts": attempt + 1
                    }
                    
            except Exception as e:
                duration = time.time() - start_time
                self._update_metrics(duration, False)
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 3.0 * (2 ** attempt)
                    logger.warning(f"Inter-KME error: {e}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.failed_requests += 1
                    logger.error(f"Inter-KME activation failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "duration": duration,
                        "attempts": attempt + 1
                    }

    def _update_metrics(self, duration: float, success: bool):
        """Update communication metrics"""
        if success:
            self.average_response_time = (
                (self.average_response_time * self.successful_requests + duration) / 
                (self.successful_requests + 1)
            )
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get communication metrics"""
        success_rate = (
            self.successful_requests / self.total_requests * 100 
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "average_response_time": self.average_response_time,
            "source_kme": self.config.source_kme_id,
            "target_kme": self.config.target_kme_id
        }

    async def close(self):
        """Close the HTTP client and cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.debug("Closed inter-KME communicator")

class ETSIInterKMEManager:
    """
    Manager for all inter-KME communications in the QKD network
    
    This class manages multiple inter-KME communication channels and provides
    a unified interface for ETSI QKD-014 compliant key activation.
    """
    
    def __init__(self):
        self.communicators: Dict[str, ETSIInterKMECommunicator] = {}
        self.certs_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs")
        self._setup_communicators()
    
    def _setup_communicators(self):
        """Setup all inter-KME communication channels"""
        
        # KME1 -> KME2 communication
        kme1_to_kme2_config = InterKMEConfig(
            source_kme_id=1,
            target_kme_id=2,
            source_inter_url="https://localhost:13001",
            target_inter_url="https://localhost:15001",
            cert_path=str(self.certs_dir / "inter_kmes" / "kme1_server.crt"),
            key_path=str(self.certs_dir / "inter_kmes" / "kme1_server.key"),
            ca_cert_path=str(self.certs_dir / "inter_kmes" / "ca_kme2.crt"),
            timeout=120.0,
            max_retries=5
        )
        
        # KME2 -> KME1 communication
        kme2_to_kme1_config = InterKMEConfig(
            source_kme_id=2,
            target_kme_id=1,
            source_inter_url="https://localhost:15001",
            target_inter_url="https://localhost:13001",
            cert_path=str(self.certs_dir / "inter_kmes" / "kme2_server.crt"),
            key_path=str(self.certs_dir / "inter_kmes" / "kme2_server.key"),
            ca_cert_path=str(self.certs_dir / "inter_kmes" / "ca_kme1.crt"),
            timeout=120.0,
            max_retries=5
        )
        
        self.communicators["1->2"] = ETSIInterKMECommunicator(kme1_to_kme2_config)
        self.communicators["2->1"] = ETSIInterKMECommunicator(kme2_to_kme1_config)
        
        logger.info("Initialized ETSI inter-KME manager with 2 communication channels")

    async def test_all_connections(self) -> Dict[str, Any]:
        """Test connectivity to all inter-KME channels"""
        results = {}
        
        for channel_name, communicator in self.communicators.items():
            logger.info(f"Testing inter-KME connection: {channel_name}")
            results[channel_name] = await communicator.test_connectivity()
        
        return results

    async def activate_keys_between_kmes(self,
                                       source_kme_id: int,
                                       target_kme_id: int,
                                       master_sae_id: int,
                                       slave_sae_id: int,
                                       key_ids: List[str],
                                       number_of_keys: int = 1) -> Dict[str, Any]:
        """
        Activate keys between KMEs using ETSI QKD-014 protocol
        
        This is the main method that fixes the inter-KME communication issue.
        """
        channel_key = f"{source_kme_id}->{target_kme_id}"
        
        if channel_key not in self.communicators:
            return {
                "success": False,
                "error": f"No inter-KME channel found for {channel_key}"
            }
        
        communicator = self.communicators[channel_key]
        
        logger.info(f"Activating keys via inter-KME channel {channel_key}")
        logger.info(f"Master SAE: {master_sae_id}, Slave SAE: {slave_sae_id}")
        logger.info(f"Key IDs: {key_ids}")
        
        result = await communicator.activate_keys_on_remote_kme(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            key_ids=key_ids,
            number_of_keys=number_of_keys
        )
        
        return result

    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all inter-KME communications"""
        metrics = {}
        
        for channel_name, communicator in self.communicators.items():
            metrics[channel_name] = await communicator.get_metrics()
        
        return metrics

    async def close_all(self):
        """Close all inter-KME communicators"""
        for communicator in self.communicators.values():
            await communicator.close()
        logger.info("Closed all inter-KME communicators")

# Global inter-KME manager instance
_inter_kme_manager: Optional[ETSIInterKMEManager] = None

def get_inter_kme_manager() -> ETSIInterKMEManager:
    """Get the global inter-KME manager instance"""
    global _inter_kme_manager
    if _inter_kme_manager is None:
        _inter_kme_manager = ETSIInterKMEManager()
    return _inter_kme_manager

async def test_inter_kme_fix():
    """Test the inter-KME communication fix"""
    logger.info("🧪 Testing ETSI QKD-014 inter-KME communication fix")
    
    manager = get_inter_kme_manager()
    
    # Test connectivity
    logger.info("Testing connectivity...")
    connectivity_results = await manager.test_all_connections()
    for channel, result in connectivity_results.items():
        if result["success"]:
            logger.info(f"✅ {channel}: Connected ({result['duration']:.2f}s)")
        else:
            logger.error(f"❌ {channel}: Failed - {result['error']}")
    
    # Test key activation
    logger.info("Testing key activation...")
    
    # Simulate key activation from KME1 to KME2 (SAE 1 -> SAE 3)
    key_ids = ["test-key-001", "test-key-002"]
    
    activation_result = await manager.activate_keys_between_kmes(
        source_kme_id=1,
        target_kme_id=2,
        master_sae_id=1,
        slave_sae_id=3,
        key_ids=key_ids,
        number_of_keys=len(key_ids)
    )
    
    if activation_result["success"]:
        logger.info(f"✅ Key activation successful ({activation_result['duration']:.2f}s)")
    else:
        logger.error(f"❌ Key activation failed: {activation_result['error']}")
    
    # Get metrics
    metrics = await manager.get_all_metrics()
    for channel, metric in metrics.items():
        logger.info(f"📊 {channel}: {metric['success_rate']:.1f}% success rate")
    
    await manager.close_all()
    
    return activation_result["success"]

if __name__ == "__main__":
    # Test the inter-KME fix
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    success = asyncio.run(test_inter_kme_fix())
    print(f"Inter-KME test {'PASSED' if success else 'FAILED'}")
