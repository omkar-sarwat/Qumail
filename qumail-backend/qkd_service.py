"""
QKD Integration Service for QuMail Secure Email
This service manages integration between QuMail backend and QKD KME servers
"""
import asyncio
import signal
import logging
import sys
import os
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('qkd_service.log')
    ]
)
logger = logging.getLogger("qkd_service")

class QKDIntegrationService:
    """Service to manage QKD KME servers for QuMail integration"""
    
    def __init__(self, kme_base_path=None, config_files=None):
        self.kme_base_path = Path(kme_base_path or r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
        self.config_files = config_files or {
            "kme1": "config_kme1.json5",
            "kme2": "config_kme2.json5"
        }
        self.processes = {}
        self.running = False
        self.status = {
            "kme1": {"status": "not_started"},
            "kme2": {"status": "not_started"}
        }
        
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _find_kme_executable(self):
        """Find the KME server executable"""
        possible_paths = [
            self.kme_base_path / "target" / "release" / "qkd_kme_server",
            self.kme_base_path / "target" / "release" / "qkd_kme_server.exe",
            self.kme_base_path / "target" / "debug" / "qkd_kme_server",
            self.kme_base_path / "target" / "debug" / "qkd_kme_server.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def start_kme_server(self, name):
        """Start a KME server with the given name"""
        if name in self.processes and self.processes[name].poll() is None:
            logger.info(f"KME server {name} is already running")
            return True
            
        if name not in self.config_files:
            logger.error(f"No configuration found for KME server {name}")
            return False
            
        config_file = self.config_files[name]
        config_path = self.kme_base_path / config_file
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return False
            
        # Find executable
        exe_path = self._find_kme_executable()
        if not exe_path:
            logger.error(f"Could not find KME server executable in {self.kme_base_path}")
            return False
            
        try:
            # Start KME server
            logger.info(f"Starting KME server {name} with config {config_file}")
            
            # Use relative path from working directory
            process = subprocess.Popen(
                [str(exe_path), str(config_file)],
                cwd=str(self.kme_base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process and update status
            self.processes[name] = process
            self.status[name] = {
                "status": "starting",
                "pid": process.pid,
                "started_at": datetime.now().isoformat(),
                "config": config_file
            }
            
            logger.info(f"KME server {name} started with PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting KME server {name}: {e}")
            return False
    
    def stop_kme_server(self, name):
        """Stop a KME server"""
        if name not in self.processes:
            logger.warning(f"KME server {name} is not running")
            return False
            
        process = self.processes[name]
        try:
            # Try to terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if didn't terminate
                process.kill()
                process.wait()
                
            logger.info(f"KME server {name} stopped")
            
            # Update status
            self.status[name] = {
                "status": "stopped",
                "stopped_at": datetime.now().isoformat()
            }
            
            # Remove from processes
            del self.processes[name]
            return True
            
        except Exception as e:
            logger.error(f"Error stopping KME server {name}: {e}")
            return False
    
    def start(self):
        """Start all KME servers"""
        logger.info("Starting QKD Integration Service")
        self.running = True
        
        # Start all KME servers
        for name in self.config_files.keys():
            self.start_kme_server(name)
        
        return True
    
    def stop(self):
        """Stop all KME servers"""
        logger.info("Stopping QKD Integration Service")
        self.running = False
        
        # Stop all running KME servers
        for name in list(self.processes.keys()):
            self.stop_kme_server(name)
        
        return True
    
    def check_status(self):
        """Check status of all KME servers"""
        for name, process in list(self.processes.items()):
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                returncode = process.poll()
                stderr = process.stderr.read() if process.stderr else ""
                
                logger.warning(f"KME server {name} has terminated with code {returncode}")
                if stderr:
                    logger.error(f"KME server {name} error output: {stderr}")
                
                # Update status
                self.status[name] = {
                    "status": "crashed",
                    "returncode": returncode,
                    "stderr": stderr,
                    "crashed_at": datetime.now().isoformat()
                }
                
                # Remove from processes
                del self.processes[name]
            else:
                # Process is running, update status
                self.status[name]["status"] = "running"
                self.status[name]["uptime"] = str(datetime.now() - datetime.fromisoformat(self.status[name]["started_at"]))
        
        return self.status
    
    async def _monitor_loop(self):
        """Monitor KME servers and restart if needed"""
        while self.running:
            try:
                # Check status of all KME servers
                status = self.check_status()
                
                # Restart any crashed servers
                for name, server_status in status.items():
                    if server_status.get("status") == "crashed":
                        logger.info(f"Restarting crashed KME server {name}")
                        self.start_kme_server(name)
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(30)
    
    async def run(self):
        """Run the service"""
        # Start servers
        self.start()
        
        # Run monitor loop
        await self._monitor_loop()

def write_status_file(service, file_path="qkd_status.json"):
    """Write service status to file"""
    try:
        status = service.check_status()
        status["timestamp"] = datetime.now().isoformat()
        
        with open(file_path, "w") as f:
            json.dump(status, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error writing status file: {e}")

async def main():
    """Main entry point"""
    logger.info("Starting QKD Integration Service")
    
    # Create service
    service = QKDIntegrationService()
    
    try:
        # Write initial status
        write_status_file(service)
        
        # Start status file writer
        async def status_writer():
            while True:
                write_status_file(service)
                await asyncio.sleep(30)
                
        # Start both tasks
        await asyncio.gather(
            service.run(),
            status_writer()
        )
        
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down...")
        service.stop()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        service.stop()

if __name__ == "__main__":
    asyncio.run(main())