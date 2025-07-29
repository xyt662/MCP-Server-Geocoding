"""地理编码提供商基类"""

from abc import ABC, abstractmethod
from typing import Optional
import httpx

from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse
from app.config import Settings


class BaseGeocodingProvider(ABC):
    """地理编码提供商基类"""
    
    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self.client = client
        self.settings = settings
        self.api_key = settings.get_api_key()
        self.base_url = settings.get_base_url()
    
    @abstractmethod
    async def geocode(self, address: str, city: Optional[str] = None) -> GeocodeResponse:
        """地理编码：将地址转换为经纬度"""
        pass
    
    @abstractmethod
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> ReverseGeocodeResponse:
        """逆地理编码：将经纬度转换为地址"""
        pass
    
    def _validate_api_key(self):
        """验证API密钥"""
        if not self.api_key:
            raise ValueError(f"缺少{self.__class__.__name__}的API密钥")