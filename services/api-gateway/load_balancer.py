"""
CloudWatch Pro - Load Balancer
"""

import time
import random
from typing import Dict, List
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class LoadBalancer:
    """Simple load balancer with metrics tracking"""
    
    def __init__(self):
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_requests = 0
        
    def record_request(self, service_name: str, response_time: float, is_error: bool = False):
        """Record request metrics"""
        self.request_counts[service_name] += 1
        self.total_requests += 1
        
        # Keep only last 100 response times for memory efficiency
        if len(self.response_times[service_name]) >= 100:
            self.response_times[service_name].pop(0)
        self.response_times[service_name].append(response_time)
        
        if is_error:
            self.error_counts[service_name] += 1
            
    def get_total_requests(self) -> int:
        """Get total number of requests"""
        return self.total_requests
        
    def get_requests_per_service(self) -> Dict[str, int]:
        """Get request count per service"""
        return dict(self.request_counts)
        
    def get_average_response_time(self, service_name: str = None) -> float:
        """Get average response time"""
        if service_name:
            times = self.response_times.get(service_name, [])
            return sum(times) / len(times) if times else 0.0
        else:
            all_times = []
            for times in self.response_times.values():
                all_times.extend(times)
            return sum(all_times) / len(all_times) if all_times else 0.0
            
    def get_error_rate(self, service_name: str = None) -> float:
        """Get error rate as percentage"""
        if service_name:
            errors = self.error_counts.get(service_name, 0)
            requests = self.request_counts.get(service_name, 0)
            return (errors / requests * 100) if requests > 0 else 0.0
        else:
            total_errors = sum(self.error_counts.values())
            return (total_errors / self.total_requests * 100) if self.total_requests > 0 else 0.0
            
    def select_instance(self, service_instances: List[str], algorithm: str = "round_robin") -> str:
        """Select service instance using load balancing algorithm"""
        if not service_instances:
            raise ValueError("No service instances available")
            
        if len(service_instances) == 1:
            return service_instances[0]
            
        if algorithm == "round_robin":
            # Simple round robin based on total requests
            return service_instances[self.total_requests % len(service_instances)]
            
        elif algorithm == "random":
            return random.choice(service_instances)
            
        elif algorithm == "least_connections":
            # Select instance with least requests
            min_requests = float('inf')
            selected_instance = service_instances[0]
            
            for instance in service_instances:
                requests = self.request_counts.get(instance, 0)
                if requests < min_requests:
                    min_requests = requests
                    selected_instance = instance
                    
            return selected_instance
            
        else:
            # Default to round robin
            return service_instances[self.total_requests % len(service_instances)]
            
    def get_health_score(self, service_name: str) -> float:
        """Calculate health score for a service (0-100)"""
        error_rate = self.get_error_rate(service_name)
        avg_response_time = self.get_average_response_time(service_name)
        
        # Health score based on error rate and response time
        error_score = max(0, 100 - error_rate * 2)  # 2% error = -4 points
        
        # Response time score (assuming 1000ms is bad, 100ms is good)
        time_score = max(0, 100 - (avg_response_time - 100) / 10)
        
        return min(100, (error_score + time_score) / 2)
        
    def get_metrics_summary(self) -> Dict:
        """Get comprehensive metrics summary"""
        return {
            "total_requests": self.total_requests,
            "requests_per_service": dict(self.request_counts),
            "average_response_times": {
                service: self.get_average_response_time(service)
                for service in self.request_counts.keys()
            },
            "error_rates": {
                service: self.get_error_rate(service)
                for service in self.request_counts.keys()
            },
            "health_scores": {
                service: self.get_health_score(service)
                for service in self.request_counts.keys()
            },
            "overall_error_rate": self.get_error_rate(),
            "overall_avg_response_time": self.get_average_response_time()
        }

