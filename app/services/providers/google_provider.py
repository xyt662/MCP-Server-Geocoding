"""Google Maps地理编码提供商"""

from typing import Optional, Dict, Any
from urllib.parse import urlencode

from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse
from app.services.providers.base_provider import BaseGeocodingProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleProvider(BaseGeocodingProvider):
    """Google Maps地理编码提供商"""
    
    def __init__(self, client, settings):
        super().__init__(client, settings)
        self._validate_api_key()
    
    async def geocode(self, address: str, city: Optional[str] = None) -> GeocodeResponse:
        """Google Maps地理编码"""
        params = {
            "key": self.api_key,
            "address": address
        }
        
        if city:
            params["address"] = f"{address}, {city}"
        
        url = f"{self.base_url}/geocode/json?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                raise Exception(f"Google Maps API错误: {data.get('status', '未知错误')}")
            
            results = data.get("results", [])
            if not results:
                raise Exception("未找到地理编码结果")
            
            result = results[0]
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            
            if not location:
                raise Exception("地理编码结果中缺少坐标信息")
            
            lat = location.get("lat")
            lng = location.get("lng")
            
            if lat is None or lng is None:
                raise Exception("坐标信息不完整")
            
            # 解析地址组件
            address_components = self._parse_address_components(result.get("address_components", []))
            
            # 计算置信度（基于location_type）
            location_type = geometry.get("location_type", "")
            confidence = self._calculate_confidence(location_type)
            
            return GeocodeResponse(
                latitude=float(lat),
                longitude=float(lng),
                formatted_address=result.get("formatted_address", address),
                confidence=confidence,
                address_components=address_components
            )
        
        except Exception as e:
            logger.error(f"Google Maps地理编码失败: {e}")
            raise
    
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> ReverseGeocodeResponse:
        """Google Maps逆地理编码"""
        params = {
            "key": self.api_key,
            "latlng": f"{latitude},{longitude}",
            "result_type": "street_address|route|neighborhood|locality|administrative_area_level_1|country"
        }
        
        url = f"{self.base_url}/geocode/json?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                raise Exception(f"Google Maps API错误: {data.get('status', '未知错误')}")
            
            results = data.get("results", [])
            if not results:
                raise Exception("未找到逆地理编码结果")
            
            result = results[0]
            formatted_address = result.get("formatted_address", "")
            
            # 解析地址组件
            address_components = self._parse_address_components(result.get("address_components", []))
            
            return ReverseGeocodeResponse(
                address=formatted_address,
                formatted_address=formatted_address,
                address_components=address_components,
                confidence=0.9,  # Google Maps逆地理编码通常比较准确
                country=address_components.get("country", ""),
                province=address_components.get("administrative_area_level_1", ""),
                city=address_components.get("locality", ""),
                district=address_components.get("administrative_area_level_2", ""),
                street=address_components.get("route", ""),
                street_number=address_components.get("street_number", ""),
                postal_code=address_components.get("postal_code", "")
            )
        
        except Exception as e:
            logger.error(f"Google Maps逆地理编码失败: {e}")
            raise
    
    def _parse_address_components(self, components: list) -> Dict[str, str]:
        """解析Google Maps地址组件"""
        parsed = {}
        
        for component in components:
            types = component.get("types", [])
            long_name = component.get("long_name", "")
            short_name = component.get("short_name", "")
            
            for type_name in types:
                parsed[type_name] = long_name
                parsed[f"{type_name}_short"] = short_name
        
        return parsed
    
    def _calculate_confidence(self, location_type: str) -> float:
        """根据Google Maps的location_type计算置信度"""
        type_confidence = {
            "ROOFTOP": 0.95,           # 精确到建筑物
            "RANGE_INTERPOLATED": 0.85, # 插值估算
            "GEOMETRIC_CENTER": 0.75,   # 几何中心
            "APPROXIMATE": 0.6          # 近似位置
        }
        
        return type_confidence.get(location_type, 0.7)