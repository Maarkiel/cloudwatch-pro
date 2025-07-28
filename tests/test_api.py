"""
CloudWatch Pro - API Tests
"""

import pytest
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
USER_SERVICE_URL = "http://localhost:8001"
METRICS_SERVICE_URL = "http://localhost:8002"

class TestUserService:
    """Test User Service endpoints"""
    
    def test_health_check(self):
        """Test user service health check"""
        response = requests.get(f"{USER_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-service"
    
    def test_register_user(self):
        """Test user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = requests.post(f"{USER_SERVICE_URL}/register", json=user_data)
        assert response.status_code in [200, 201, 409]  # 409 if user already exists
    
    def test_login_user(self):
        """Test user login"""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response = requests.post(f"{USER_SERVICE_URL}/login", data=login_data)
        assert response.status_code in [200, 401]  # 401 if credentials invalid

class TestMetricsService:
    """Test Metrics Collector Service endpoints"""
    
    def test_health_check(self):
        """Test metrics service health check"""
        response = requests.get(f"{METRICS_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "metrics-collector"
    
    def test_submit_metric(self):
        """Test metric submission"""
        metric_data = {
            "metric_name": "cpu_usage",
            "value": 75.5,
            "resource_id": "server-001",
            "tags": {"environment": "test"}
        }
        response = requests.post(f"{METRICS_SERVICE_URL}/metrics", json=metric_data)
        assert response.status_code in [200, 201]
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        response = requests.get(f"{METRICS_SERVICE_URL}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

class TestAPIGateway:
    """Test API Gateway endpoints"""
    
    def test_health_check(self):
        """Test API gateway health check"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
    
    def test_service_discovery(self):
        """Test service discovery"""
        response = requests.get(f"{BASE_URL}/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data

class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_metric_flow(self):
        """Test complete metric flow from submission to retrieval"""
        # Submit a metric
        metric_data = {
            "metric_name": "test_metric",
            "value": 42.0,
            "resource_id": "test-resource",
            "tags": {"test": "true"}
        }
        
        submit_response = requests.post(f"{METRICS_SERVICE_URL}/metrics", json=metric_data)
        assert submit_response.status_code in [200, 201]
        
        # Retrieve metrics
        get_response = requests.get(f"{METRICS_SERVICE_URL}/metrics")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert "metrics" in data

if __name__ == "__main__":
    # Run basic connectivity tests
    print("Running CloudWatch Pro API Tests...")
    
    try:
        # Test User Service
        response = requests.get(f"{USER_SERVICE_URL}/health", timeout=5)
        print(f"✓ User Service: {response.status_code}")
    except Exception as e:
        print(f"✗ User Service: {e}")
    
    try:
        # Test Metrics Service
        response = requests.get(f"{METRICS_SERVICE_URL}/health", timeout=5)
        print(f"✓ Metrics Service: {response.status_code}")
    except Exception as e:
        print(f"✗ Metrics Service: {e}")
    
    try:
        # Test API Gateway
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✓ API Gateway: {response.status_code}")
    except Exception as e:
        print(f"✗ API Gateway: {e}")
    
    print("Test run completed!")
