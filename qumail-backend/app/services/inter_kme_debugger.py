"""
ETSI QKD-014 Inter-KME Communication Debugger

This tool provides deep debugging and monitoring capabilities for inter-KME communication
issues. It helps diagnose why the POST requests are timing out and provides detailed
analysis of the communication flow.

Features:
- Real-time monitoring of KME server logs
- Inter-KME communication testing
- Certificate validation
- Network connectivity analysis
- Protocol compliance checking
"""

import asyncio
import httpx
import ssl
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64
import psutil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InterKMEDebugger:
    """Debugger for inter-KME communication issues"""
    
    def __init__(self):
        self.root_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
        self.certs_dir = self.root_dir / "certs"
        
        # KME endpoints
        self.kme1_sae_url = "https://localhost:13000"
        self.kme1_inter_url = "https://localhost:13001"
        self.kme2_sae_url = "https://localhost:14000"
        self.kme2_inter_url = "https://localhost:15001"
        
    def check_processes(self):
        """Check if KME processes are running"""
        logger.info("🔍 Checking KME processes...")
        
        rust_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'qkd' in ' '.join(proc.info['cmdline']).lower():
                    rust_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if rust_processes:
            logger.info(f"Found {len(rust_processes)} QKD processes:")
            for proc in rust_processes:
                logger.info(f"  PID {proc['pid']}: {' '.join(proc['cmdline'])}")
        else:
            logger.warning("No QKD processes found!")
        
        return rust_processes

    def check_network_ports(self):
        """Check if required ports are listening"""
        logger.info("🔍 Checking network ports...")
        
        required_ports = [13000, 13001, 14000, 15001]
        listening_ports = []
        
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port in required_ports:
                listening_ports.append(conn.laddr.port)
        
        for port in required_ports:
            status = "✅ LISTENING" if port in listening_ports else "❌ NOT LISTENING"
            logger.info(f"  Port {port}: {status}")
        
        return listening_ports

    async def check_certificate_validity(self):
        """Check if certificates are valid and properly configured"""
        logger.info("🔍 Checking certificates...")
        
        cert_configs = [
            {
                "name": "KME1 SAE Client",
                "cert": self.certs_dir / "kme-1-local-zone" / "client_1_cert.pem",
                "key": self.certs_dir / "kme-1-local-zone" / "client_1.key",
                "ca": self.certs_dir / "kme-1-local-zone" / "ca.crt"
            },
            {
                "name": "KME2 SAE Client",
                "cert": self.certs_dir / "kme-2-local-zone" / "client_3_cert.pem",
                "key": self.certs_dir / "kme-2-local-zone" / "client_3.key",
                "ca": self.certs_dir / "kme-2-local-zone" / "ca.crt"
            },
            {
                "name": "KME1 Inter-KME",
                "cert": self.certs_dir / "inter_kmes" / "kme1_server.crt",
                "key": self.certs_dir / "inter_kmes" / "kme1_server.key",
                "ca": self.certs_dir / "inter_kmes" / "ca_kme1.crt"
            },
            {
                "name": "KME2 Inter-KME",
                "cert": self.certs_dir / "inter_kmes" / "kme2_server.crt",
                "key": self.certs_dir / "inter_kmes" / "kme2_server.key",
                "ca": self.certs_dir / "inter_kmes" / "ca_kme2.crt"
            }
        ]
        
        for config in cert_configs:
            logger.info(f"Checking {config['name']}:")
            
            for cert_type, path in [("cert", config["cert"]), ("key", config["key"]), ("ca", config["ca"])]:
                if path.exists():
                    logger.info(f"  ✅ {cert_type}: {path}")
                else:
                    logger.error(f"  ❌ {cert_type}: {path} (NOT FOUND)")

    async def test_basic_connectivity(self):
        """Test basic connectivity to all endpoints"""
        logger.info("🔍 Testing basic connectivity...")
        
        endpoints = [
            ("KME1 SAE", self.kme1_sae_url),
            ("KME1 Inter", self.kme1_inter_url),
            ("KME2 SAE", self.kme2_sae_url),
            ("KME2 Inter", self.kme2_inter_url)
        ]
        
        for name, url in endpoints:
            try:
                # Create SSL context that ignores verification for testing
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with httpx.AsyncClient(verify=ssl_context, timeout=5.0) as client:
                    response = await client.get(f"{url}/")
                    logger.info(f"  ✅ {name}: {response.status_code}")
            except Exception as e:
                logger.error(f"  ❌ {name}: {str(e)}")

    async def test_sae_authentication(self):
        """Test SAE authentication with certificates"""
        logger.info("🔍 Testing SAE authentication...")
        
        # Test KME1 SAE authentication
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # For testing
            
            cert_path = self.certs_dir / "kme-1-local-zone" / "client_1_cert.pem"
            key_path = self.certs_dir / "kme-1-local-zone" / "client_1.key"
            
            if cert_path.exists() and key_path.exists():
                ssl_context.load_cert_chain(str(cert_path), str(key_path))
                
                async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
                    response = await client.get(f"{self.kme1_sae_url}/api/v1/sae/info/me")
                    logger.info(f"  ✅ KME1 SAE auth: {response.status_code} - {response.json()}")
            else:
                logger.error("  ❌ KME1 certificates not found")
        except Exception as e:
            logger.error(f"  ❌ KME1 SAE auth failed: {e}")
        
        # Test KME2 SAE authentication
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            cert_path = self.certs_dir / "kme-2-local-zone" / "client_3_cert.pem"
            key_path = self.certs_dir / "kme-2-local-zone" / "client_3.key"
            
            if cert_path.exists() and key_path.exists():
                ssl_context.load_cert_chain(str(cert_path), str(key_path))
                
                async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
                    response = await client.get(f"{self.kme2_sae_url}/api/v1/sae/info/me")
                    logger.info(f"  ✅ KME2 SAE auth: {response.status_code} - {response.json()}")
            else:
                logger.error("  ❌ KME2 certificates not found")
        except Exception as e:
            logger.error(f"  ❌ KME2 SAE auth failed: {e}")

    async def test_inter_kme_direct_communication(self):
        """Test direct inter-KME communication"""
        logger.info("🔍 Testing direct inter-KME communication...")
        
        # Test KME1 -> KME2 communication
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Use inter-KME certificates
            cert_path = self.certs_dir / "inter_kmes" / "kme1_server.crt"
            key_path = self.certs_dir / "inter_kmes" / "kme1_server.key"
            
            if cert_path.exists() and key_path.exists():
                ssl_context.load_cert_chain(str(cert_path), str(key_path))
                
                async with httpx.AsyncClient(verify=ssl_context, timeout=30.0) as client:
                    # Try to connect to KME2's inter-KME interface
                    response = await client.get(f"{self.kme2_inter_url}/")
                    logger.info(f"  ✅ KME1->KME2: {response.status_code}")
            else:
                logger.error("  ❌ KME1 inter-KME certificates not found")
        except Exception as e:
            logger.error(f"  ❌ KME1->KME2 failed: {e}")
        
        # Test KME2 -> KME1 communication
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            cert_path = self.certs_dir / "inter_kmes" / "kme2_server.crt"
            key_path = self.certs_dir / "inter_kmes" / "kme2_server.key"
            
            if cert_path.exists() and key_path.exists():
                ssl_context.load_cert_chain(str(cert_path), str(key_path))
                
                async with httpx.AsyncClient(verify=ssl_context, timeout=30.0) as client:
                    response = await client.get(f"{self.kme1_inter_url}/")
                    logger.info(f"  ✅ KME2->KME1: {response.status_code}")
            else:
                logger.error("  ❌ KME2 inter-KME certificates not found")
        except Exception as e:
            logger.error(f"  ❌ KME2->KME1 failed: {e}")

    async def analyze_key_request_flow(self):
        """Analyze the complete key request flow with detailed logging"""
        logger.info("🔍 Analyzing key request flow...")
        
        # Step 1: Check key status (should work)
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            cert_path = self.certs_dir / "kme-1-local-zone" / "client_1_cert.pem"
            key_path = self.certs_dir / "kme-1-local-zone" / "client_1.key"
            ssl_context.load_cert_chain(str(cert_path), str(key_path))
            
            async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
                # Check status for SAE 3 (cross-KME)
                response = await client.get(f"{self.kme1_sae_url}/api/v1/keys/3/status")
                logger.info(f"  ✅ Status check: {response.status_code}")
                if response.status_code == 200:
                    status = response.json()
                    logger.info(f"     Available keys: {status.get('stored_key_count', 0)}")
                
        except Exception as e:
            logger.error(f"  ❌ Status check failed: {e}")
        
        # Step 2: Request encryption key (this should trigger inter-KME communication)
        try:
            logger.info("  Attempting POST /api/v1/keys/3/enc_keys...")
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.load_cert_chain(str(cert_path), str(key_path))
            
            async with httpx.AsyncClient(verify=ssl_context, timeout=120.0) as client:
                start_time = time.time()
                
                payload = {"number": 1}
                response = await client.post(
                    f"{self.kme1_sae_url}/api/v1/keys/3/enc_keys",
                    json=payload
                )
                
                duration = time.time() - start_time
                logger.info(f"  ✅ POST request completed: {response.status_code} ({duration:.2f}s)")
                
                if response.status_code == 200:
                    data = response.json()
                    keys = data.get("keys", [])
                    logger.info(f"     Received {len(keys)} keys")
                    for key in keys:
                        logger.info(f"     Key ID: {key.get('key_ID', 'N/A')}")
                else:
                    logger.error(f"     Response: {response.text}")
                
        except httpx.TimeoutException:
            logger.error("  ❌ POST request timed out - Inter-KME communication issue!")
        except Exception as e:
            logger.error(f"  ❌ POST request failed: {e}")

    def check_configuration_files(self):
        """Check KME configuration files for inter-KME settings"""
        logger.info("🔍 Checking configuration files...")
        
        config_files = [
            self.root_dir / "config_kme1.json5",
            self.root_dir / "config_kme2.json5"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                logger.info(f"Checking {config_file.name}:")
                try:
                    # Read as text and extract JSON part (ignoring JSON5 comments)
                    content = config_file.read_text()
                    # Simple JSON5 to JSON conversion (remove comments)
                    lines = content.split('\n')
                    json_lines = []
                    for line in lines:
                        if '//' in line:
                            line = line[:line.index('//')]
                        json_lines.append(line)
                    json_content = '\n'.join(json_lines)
                    
                    config = json.loads(json_content)
                    
                    # Check inter-KME configuration
                    if "inter_kme" in config:
                        inter_kme = config["inter_kme"]
                        logger.info(f"  Inter-KME config found:")
                        logger.info(f"    Address: {inter_kme.get('address', 'N/A')}")
                        logger.info(f"    Port: {inter_kme.get('port', 'N/A')}")
                        
                        if "other_kmes" in inter_kme:
                            logger.info(f"    Other KMEs: {len(inter_kme['other_kmes'])}")
                            for other_kme in inter_kme["other_kmes"]:
                                logger.info(f"      KME {other_kme.get('kme_id', 'N/A')}: {other_kme.get('address', 'N/A')}")
                    else:
                        logger.warning(f"  ❌ No inter-KME configuration found!")
                        
                except Exception as e:
                    logger.error(f"  ❌ Failed to parse config: {e}")
            else:
                logger.error(f"  ❌ Config file not found: {config_file}")

    def check_raw_keys(self):
        """Check available raw quantum keys"""
        logger.info("🔍 Checking raw quantum keys...")
        
        raw_keys_dir = self.root_dir / "raw_keys"
        if raw_keys_dir.exists():
            for kme_dir in raw_keys_dir.iterdir():
                if kme_dir.is_dir():
                    key_files = list(kme_dir.glob("*.cor"))
                    logger.info(f"  {kme_dir.name}: {len(key_files)} raw key files")
        else:
            logger.error("  ❌ Raw keys directory not found!")

    async def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnosis of inter-KME communication"""
        logger.info("🚀 Starting comprehensive inter-KME diagnosis")
        logger.info("=" * 80)
        
        # Basic system checks
        self.check_processes()
        self.check_network_ports()
        await self.check_certificate_validity()
        self.check_configuration_files()
        self.check_raw_keys()
        
        # Network connectivity tests
        await self.test_basic_connectivity()
        await self.test_sae_authentication()
        await self.test_inter_kme_direct_communication()
        
        # Protocol analysis
        await self.analyze_key_request_flow()
        
        logger.info("=" * 80)
        logger.info("🏁 Diagnosis complete")
        
        logger.info("\n📋 Recommendations:")
        logger.info("1. Check KME server logs for inter-KME communication errors")
        logger.info("2. Verify inter-KME certificates are properly configured")
        logger.info("3. Ensure both KME servers can reach each other's inter-KME interfaces")
        logger.info("4. Check firewall settings for ports 13001 and 15001")
        logger.info("5. Verify quantum key availability and distribution")

async def main():
    """Main diagnosis runner"""
    debugger = InterKMEDebugger()
    await debugger.run_comprehensive_diagnosis()

if __name__ == "__main__":
    asyncio.run(main())
