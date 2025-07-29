"""地理编码服务核心实现"""

import asyncio
import time
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from cachetools import TTLCache

from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse
from app.config import get_settings
from app.utils.logger import get_logger
from app.services.providers.amap_provider import AmapProvider
from app.services.providers.baidu_provider import BaiduProvider
from app.services.providers.google_provider import GoogleProvider

logger = get_logger(__name__)
settings = get_settings()


class GeocodingService:
    """地理编码服务类"""
    
    def __init__(self):
        self.settings = settings
        self.client: Optional[httpx.AsyncClient] = None
        self.provider = None
        self.start_time = time.time()
        
        # 初始化缓存
        if self.settings.CACHE_ENABLED:
            self.cache = TTLCache(
                maxsize=self.settings.CACHE_MAX_SIZE,
                ttl=self.settings.CACHE_TTL
            )
        else:
            self.cache = None
    
    async def initialize(self):
        """初始化服务"""
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.GEOCODING_TIMEOUT),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # 初始化地理编码提供商
        provider_name = self.settings.GEOCODING_PROVIDER.lower()
        if provider_name == "amap":
            self.provider = AmapProvider(self.client, self.settings)
        elif provider_name == "baidu":
            self.provider = BaiduProvider(self.client, self.settings)
        elif provider_name == "google":
            self.provider = GoogleProvider(self.client, self.settings)
        else:
            raise ValueError(f"不支持的地理编码提供商: {provider_name}")
        
        logger.info(f"地理编码服务初始化完成，使用提供商: {provider_name}")
    
    async def close(self):
        """关闭服务"""
        if self.client:
            await self.client.aclose()
            logger.info("HTTP客户端已关闭")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.client or not self.provider:
                return False
            
            # 简单的连通性测试
            response = await self.client.get("https://httpbin.org/status/200", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [operation]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    async def geocode(self, address: str, city: Optional[str] = None) -> GeocodeResponse:
        """地理编码：将地址转换为经纬度"""
        # 检查缓存
        cache_key = None
        if self.cache:
            cache_key = self._get_cache_key("geocode", address=address, city=city or "")
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"从缓存获取地理编码结果: {address}")
                return cached_result
        
        # 执行地理编码
        retry_count = 0
        last_exception = None
        
        while retry_count < self.settings.GEOCODING_RETRY_TIMES:
            try:
                result = await self.provider.geocode(address, city)
                
                # 缓存结果
                if self.cache and cache_key:
                    self.cache[cache_key] = result
                
                return result
            
            except Exception as e:
                last_exception = e
                retry_count += 1
                if retry_count < self.settings.GEOCODING_RETRY_TIMES:
                    wait_time = 2 ** retry_count  # 指数退避
                    logger.warning(f"地理编码失败，{wait_time}秒后重试 ({retry_count}/{self.settings.GEOCODING_RETRY_TIMES}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"地理编码最终失败: {address}, 错误: {e}")
        
        raise last_exception or Exception("地理编码失败")
    
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> ReverseGeocodeResponse:
        """逆地理编码：将经纬度转换为地址"""
        # 检查缓存
        cache_key = None
        if self.cache:
            cache_key = self._get_cache_key(
                "reverse_geocode", 
                lat=round(latitude, 6), 
                lng=round(longitude, 6), 
                radius=radius
            )
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"从缓存获取逆地理编码结果: {latitude}, {longitude}")
                return cached_result
        
        # 执行逆地理编码
        retry_count = 0
        last_exception = None
        
        while retry_count < self.settings.GEOCODING_RETRY_TIMES:
            try:
                result = await self.provider.reverse_geocode(latitude, longitude, radius)
                
                # 缓存结果
                if self.cache and cache_key:
                    self.cache[cache_key] = result
                
                return result
            
            except Exception as e:
                last_exception = e
                retry_count += 1
                if retry_count < self.settings.GEOCODING_RETRY_TIMES:
                    wait_time = 2 ** retry_count  # 指数退避
                    logger.warning(f"逆地理编码失败，{wait_time}秒后重试 ({retry_count}/{self.settings.GEOCODING_RETRY_TIMES}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"逆地理编码最终失败: {latitude}, {longitude}, 错误: {e}")
        
        raise last_exception or Exception("逆地理编码失败")
    
    def get_uptime(self) -> float:
        """获取服务运行时间"""
        return time.time() - self.start_time
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hits": getattr(self.cache, 'hits', 0),
            "misses": getattr(self.cache, 'misses', 0)
        }