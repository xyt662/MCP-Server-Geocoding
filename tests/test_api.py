"""API接口测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse

client = TestClient(app)


class TestHealthCheck:
    """健康检查测试"""
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    @patch('app.main.get_geocoding_service')
    def test_health_check_success(self, mock_get_service):
        """测试健康检查成功"""
        mock_service = AsyncMock()
        mock_service.health_check.return_value = True
        mock_get_service.return_value = mock_service
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('app.main.get_geocoding_service')
    def test_health_check_failure(self, mock_get_service):
        """测试健康检查失败"""
        mock_service = AsyncMock()
        mock_service.health_check.return_value = False
        mock_get_service.return_value = mock_service
        
        response = client.get("/health")
        assert response.status_code == 503


class TestGeocoding:
    """地理编码测试"""
    
    @patch('app.main.get_geocoding_service')
    def test_geocode_success(self, mock_get_service):
        """测试地理编码成功"""
        mock_service = AsyncMock()
        mock_response = GeocodeResponse(
            latitude=39.9042,
            longitude=116.4074,
            formatted_address="北京市朝阳区三里屯",
            confidence=0.9
        )
        mock_service.geocode.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        response = client.post("/geocode", json={
            "address": "北京市朝阳区三里屯"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["latitude"] == 39.9042
        assert data["longitude"] == 116.4074
        assert "三里屯" in data["formatted_address"]
    
    def test_geocode_invalid_request(self):
        """测试地理编码无效请求"""
        response = client.post("/geocode", json={
            "address": ""
        })
        assert response.status_code == 422
    
    @patch('app.main.get_geocoding_service')
    def test_geocode_service_error(self, mock_get_service):
        """测试地理编码服务错误"""
        mock_service = AsyncMock()
        mock_service.geocode.side_effect = Exception("API错误")
        mock_get_service.return_value = mock_service
        
        response = client.post("/geocode", json={
            "address": "无效地址"
        })
        assert response.status_code == 400


class TestReverseGeocoding:
    """逆地理编码测试"""
    
    @patch('app.main.get_geocoding_service')
    def test_reverse_geocode_success(self, mock_get_service):
        """测试逆地理编码成功"""
        mock_service = AsyncMock()
        mock_response = ReverseGeocodeResponse(
            address="北京市朝阳区三里屯",
            formatted_address="北京市朝阳区三里屯",
            confidence=0.9,
            country="中国",
            province="北京市",
            city="北京市",
            district="朝阳区"
        )
        mock_service.reverse_geocode.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        response = client.post("/reverse-geocode", json={
            "latitude": 39.9042,
            "longitude": 116.4074
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "三里屯" in data["address"]
        assert data["country"] == "中国"
    
    def test_reverse_geocode_invalid_coordinates(self):
        """测试逆地理编码无效坐标"""
        response = client.post("/reverse-geocode", json={
            "latitude": 91,  # 无效纬度
            "longitude": 116.4074
        })
        assert response.status_code == 422
    
    @patch('app.main.get_geocoding_service')
    def test_reverse_geocode_service_error(self, mock_get_service):
        """测试逆地理编码服务错误"""
        mock_service = AsyncMock()
        mock_service.reverse_geocode.side_effect = Exception("API错误")
        mock_get_service.return_value = mock_service
        
        response = client.post("/reverse-geocode", json={
            "latitude": 39.9042,
            "longitude": 116.4074
        })
        assert response.status_code == 400


class TestCORS:
    """CORS测试"""
    
    def test_cors_headers(self):
        """测试CORS头部"""
        response = client.options("/")
        assert response.status_code == 200
        # 注意：TestClient可能不会完全模拟CORS行为
        # 在实际部署中需要进行集成测试