"""
CloudWatch Pro - Service Discovery
"""

import asyncio
import logging
from typing import Dict, List, Optional
import httpx
import redis
from config import settings

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Service discovery and health checking"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
        self.services: Dict[str, Dict] = {}
        
    async def initialize(self):
        """Initialize service discovery"""
        logger.info("Initializing service discovery...")
        
        # Register known services
        await self.register_service("user-service", "user-service", 8001)
        await self.register_service("metrics-collector", "metrics-collector", 8002)
        
    async def register_service(self, name: str, host: str, port: int, health_check_url: str = "/health"):
        """Register a service"""
        service_info = {
            "name": name,
            "host": host,
            "port": port,
            "url": f"http://{host}:{port}",
            "health_check_url": health_check_url,
            "status": "unknown",
            "last_check": None
        }
        
        self.services[name] = service_info
        
        # Store in Redis
        self.redis_client.hset(
            f"service:{name}",
            mapping={
                "host": host,
                "port": port,
                "url": service_info["url"],
                "health_check_url": health_check_url,
                "status": "registered"
            }
        )
        
        logger.info(f"Registered service: {name} at {service_info['url']}")
        
    async def deregister_service(self, name: str):
        """Deregister a service"""
        if name in self.services:
            del self.services[name]
            
        self.redis_client.delete(f"service:{name}")
        logger.info(f"Deregistered service: {name}")
        
    async def get_service_url(self, name: str) -> Optional[str]:
        """Get service URL by name"""
        if name in self.services:
            service = self.services[name]
            if service["status"] == "healthy":
                return service["url"]
                
        # Try to get from Redis
        service_data = self.redis_client.hgetall(f"service:{name}")
        if service_data:
            return service_data.get("url")
            
        return None
        
    async def list_services(self) -> List[Dict]:
        """List all registered services"""
        services = []
        
        for name, service in self.services.items():
            services.append({
                "name": name,
                "url": service["url"],
                "status": service["status"],
                "last_check": service["last_check"]
            })
            
        return services
        
    async def health_check(self, name: str) -> bool:
        """Perform health check on a service"""
        if name not in self.services:
            return False
            
        service = self.services[name]
        health_url = f"{service['url']}{service['health_check_url']}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                is_healthy = response.status_code == 200
                
                service["status"] = "healthy" if is_healthy else "unhealthy"
                service["last_check"] = asyncio.get_event_loop().time()
                
                # Update Redis
                self.redis_client.hset(
                    f"service:{name}",
                    "status",
                    service["status"]
                )
                
                return is_healthy
                
        except Exception as e:
            logger.warning(f"Health check failed for {name}: {e}")
            service["status"] = "unhealthy"
            service["last_check"] = asyncio.get_event_loop().time()
            
            self.redis_client.hset(
                f"service:{name}",
                "status",
                "unhealthy"
            )
            
            return False
            
    async def health_check_all(self):
        """Perform health check on all services"""
        tasks = []
        for name in self.services:
            tasks.append(self.health_check(name))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def start_health_monitoring(self):
        """Start periodic health monitoring"""
        while True:
            try:
                await self.health_check_all()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

