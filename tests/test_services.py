"""服务层测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.geocoding_service import GeocodingService
from app.services.providers.amap_provider import AmapProvider
from app.config import Settings
from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse


class TestGeocodingService:
    """地理编码服务测试"""
    
    @pytest.fixture
    def mock_settings(self):
        """模拟配置"""
        settings = MagicMock(spec=Settings)
        settings.GEOCODING_PROVIDER = "amap"
        settings.GEOCODING_TIMEOUT = 10
        settings.GEOCODING_RETRY_TIMES = 3
        settings.CACHE_ENABLED = True
        settings.CACHE_TTL = 3600
        settings.CACHE_MAX_SIZE = 1000
        return settings
    
    @pytest.fixture
    def mock_client(self):
        """模拟HTTP客户端"""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    async def service(self, mock_settings):
        """创建服务实例"""
        with patch('app.services.geocoding_service.get_settings', return_value=mock_settings):
            service = GeocodingService()
            yield service
            if service.client:
                await service.close()
    
    @pytest.mark.asyncio
    async def test_initialize_service(self, service, mock_settings):
        """测试服务初始化"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            with patch('app.services.providers.amap_provider.AmapProvider') as mock_provider_class:
                mock_provider = AsyncMock()
                mock_provider_class.return_value = mock_provider
                
                await service.initialize()
                
                assert service.client is not None
                assert service.provider is not None
                mock_client_class.assert_called_once()
                mock_provider_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """测试健康检查成功"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        
        service.client = mock_client
        service.provider = AsyncMock()
        
        result = await service.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """测试健康检查失败"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("连接失败")
        
        service.client = mock_client
        service.provider = AsyncMock()
        
        result = await service.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_geocode_success(self, service):
        """测试地理编码成功"""
        mock_provider = AsyncMock()
        expected_response = GeocodeResponse(
            latitude=39.9042,
            longitude=116.4074,
            formatted_address="北京市朝阳区三里屯",
            confidence=0.9
        )
        mock_provider.geocode.return_value = expected_response
        
        service.provider = mock_provider
        service.cache = None  # 禁用缓存以简化测试
        
        result = await service.geocode("北京市朝阳区三里屯")
        
        assert result == expected_response
        mock_provider.geocode.assert_called_once_with("北京市朝阳区三里屯", None)
    
    @pytest.mark.asyncio
    async def test_geocode_with_retry(self, service, mock_settings):
        """测试地理编码重试机制"""
        mock_provider = AsyncMock()
        # 前两次失败，第三次成功
        mock_provider.geocode.side_effect = [
            Exception("临时错误"),
            Exception("临时错误"),
            GeocodeResponse(
                latitude=39.9042,
                longitude=116.4074,
                formatted_address="北京市朝阳区三里屯",
                confidence=0.9
            )
        ]
        
        service.provider = mock_provider
        service.cache = None
        
        with patch('asyncio.sleep'):  # 跳过实际的等待时间
            result = await service.geocode("北京市朝阳区三里屯")
        
        assert result.latitude == 39.9042
        assert mock_provider.geocode.call_count == 3
    
    @pytest.mark.asyncio
    async def test_geocode_max_retries_exceeded(self, service, mock_settings):
        """测试地理编码超过最大重试次数"""
        mock_provider = AsyncMock()
        mock_provider.geocode.side_effect = Exception("持续错误")
        
        service.provider = mock_provider
        service.cache = None
        
        with patch('asyncio.sleep'):  # 跳过实际的等待时间
            with pytest.raises(Exception, match="持续错误"):
                await service.geocode("无效地址")
        
        assert mock_provider.geocode.call_count == mock_settings.GEOCODING_RETRY_TIMES
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self, service):
        """测试逆地理编码成功"""
        mock_provider = AsyncMock()
        expected_response = ReverseGeocodeResponse(
            address="北京市朝阳区三里屯",
            formatted_address="北京市朝阳区三里屯",
            confidence=0.9
        )
        mock_provider.reverse_geocode.return_value = expected_response
        
        service.provider = mock_provider
        service.cache = None
        
        result = await service.reverse_geocode(39.9042, 116.4074)
        
        assert result == expected_response
        mock_provider.reverse_geocode.assert_called_once_with(39.9042, 116.4074, 1000)
    
    def test_cache_key_generation(self, service):
        """测试缓存键生成"""
        key1 = service._get_cache_key("geocode", address="北京", city="")
        key2 = service._get_cache_key("geocode", address="北京", city="")
        key3 = service._get_cache_key("geocode", address="上海", city="")
        
        assert key1 == key2
        assert key1 != key3
        assert "geocode" in key1
        assert "北京" in key1
    
    def test_get_uptime(self, service):
        """测试获取运行时间"""
        uptime = service.get_uptime()
        assert isinstance(uptime, float)
        assert uptime >= 0
    
    def test_get_cache_stats_disabled(self, service):
        """测试获取缓存统计（缓存禁用）"""
        service.cache = None
        stats = service.get_cache_stats()
        assert stats["enabled"] is False
    
    def test_get_cache_stats_enabled(self, service):
        """测试获取缓存统计（缓存启用）"""
        from cachetools import TTLCache
        service.cache = TTLCache(maxsize=100, ttl=3600)
        
        stats = service.get_cache_stats()
        assert stats["enabled"] is True
        assert stats["max_size"] == 100
        assert stats["ttl"] == 3600


class TestAmapProvider:
    """高德地图提供商测试"""
    
    @pytest.fixture
    def mock_settings(self):
        """模拟配置"""
        settings = MagicMock()
        settings.get_api_key.return_value = "test_api_key"
        settings.get_base_url.return_value = "https://restapi.amap.com/v3"
        return settings
    
    @pytest.fixture
    def provider(self, mock_settings):
        """创建提供商实例"""
        mock_client = AsyncMock()
        return AmapProvider(mock_client, mock_settings)
    
    @pytest.mark.asyncio
    async def test_geocode_success(self, provider):
        """测试高德地图地理编码成功"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "geocodes": [{
                "location": "116.4074,39.9042",
                "formatted_address": "北京市朝阳区三里屯",
                "level": "兴趣点",
                "country": "中国",
                "province": "北京市",
                "city": "北京市",
                "district": "朝阳区"
            }]
        }
        provider.client.get.return_value = mock_response
        
        result = await provider.geocode("北京市朝阳区三里屯")
        
        assert result.latitude == 39.9042
        assert result.longitude == 116.4074
        assert "三里屯" in result.formatted_address
        assert result.confidence > 0
    
    @pytest.mark.asyncio
    async def test_geocode_api_error(self, provider):
        """测试高德地图API错误"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "0",
            "info": "INVALID_USER_KEY"
        }
        provider.client.get.return_value = mock_response
        
        with pytest.raises(Exception, match="高德地图API错误"):
            await provider.geocode("无效地址")
    
    def test_calculate_confidence(self, provider):
        """测试置信度计算"""
        assert provider._calculate_confidence("门牌号") == 0.95
        assert provider._calculate_confidence("兴趣点") == 0.9
        assert provider._calculate_confidence("市") == 0.5
        assert provider._calculate_confidence("未知级别") == 0.7