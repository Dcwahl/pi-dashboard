import json
import httpx
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ServiceHealthChecker:
    """Monitor health of external services defined in services.json"""
    
    def __init__(self, config_path: str = "services.json"):
        self.config_path = Path(config_path)
        self.services: List[Dict] = []
        self.health_status: Dict[str, Dict] = {}
        self.load_services()
    
    def load_services(self):
        """Load services from config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.services = config.get('services', [])
                    print(f"Loaded {len(self.services)} services from config")
            else:
                print(f"Config file not found: {self.config_path}")
                self.services = []
        except Exception as e:
            print(f"Error loading services config: {e}")
            self.services = []
    
    async def check_service_health(self, service: Dict) -> Dict:
        """Check health of a single service"""
        name = service.get('name', 'Unknown')
        url = service.get('url', '')
        health_endpoint = service.get('health_endpoint', '/health')
        
        # Build full health URL
        full_url = f"{url.rstrip('/')}{health_endpoint}"
        
        result = {
            'name': name,
            'url': url,
            'health_endpoint': health_endpoint,
            'status': 'unknown',
            'response_time_ms': None,
            'last_check': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(full_url)
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                result['response_time_ms'] = round(response_time, 2)
                
                # Consider 2xx status codes as healthy
                if 200 <= response.status_code < 300:
                    result['status'] = 'healthy'
                else:
                    result['status'] = 'unhealthy'
                    result['error'] = f"HTTP {response.status_code}"
                    
        except httpx.TimeoutException:
            result['status'] = 'unhealthy'
            result['error'] = 'Timeout'
        except httpx.ConnectError:
            result['status'] = 'unhealthy'
            result['error'] = 'Connection refused'
        except Exception as e:
            result['status'] = 'unhealthy'
            result['error'] = str(e)
        
        return result
    
    async def check_all_services(self):
        """Check health of all enabled services"""
        enabled_services = [s for s in self.services if s.get('enabled', True)]
        
        if not enabled_services:
            return
        
        # Check all services concurrently
        tasks = [self.check_service_health(service) for service in enabled_services]
        results = await asyncio.gather(*tasks)
        
        # Update health status
        for result in results:
            self.health_status[result['name']] = result
    
    def get_all_health_status(self) -> List[Dict]:
        """Get health status of all services"""
        return list(self.health_status.values())
    
    def get_service_health(self, service_name: str) -> Optional[Dict]:
        """Get health status of a specific service"""
        return self.health_status.get(service_name)


# Global instance
service_health_checker = ServiceHealthChecker()
