"""百度地图地理编码提供商"""

from typing import Optional, Dict, Any
from urllib.parse import urlencode

from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse
from app.services.providers.base_provider import BaseGeocodingProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaiduProvider(BaseGeocodingProvider):
    """百度地图地理编码提供商"""
    
    def __init__(self, client, settings):
        super().__init__(client, settings)
        self._validate_api_key()
    
    async def geocode(self, address: str, city: Optional[str] = None) -> GeocodeResponse:
        """百度地图地理编码"""
        params = {
            "ak": self.api_key,
            "address": address,
            "output": "json"
        }
        
        if city:
            params["city"] = city
        
        url = f"{self.base_url}/geocoding/v3/?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != 0:
                raise Exception(f"百度地图API错误: {data.get('message', '未知错误')}")
            
            result = data.get("result", {})
            location = result.get("location", {})
            
            if not location:
                raise Exception("地理编码结果中缺少坐标信息")
            
            lat = location.get("lat")
            lng = location.get("lng")
            
            if lat is None or lng is None:
                raise Exception("坐标信息不完整")
            
            # 构建地址组件
            address_components = {
                "country": "中国",
                "province": "",
                "city": "",
                "district": "",
                "street": "",
                "confidence": result.get("confidence", 0),
                "comprehension": result.get("comprehension", 0),
                "level": result.get("level", "")
            }
            
            # 计算置信度
            confidence = result.get("confidence", 0) / 100.0  # 百度返回0-100，转换为0-1
            
            return GeocodeResponse(
                latitude=float(lat),
                longitude=float(lng),
                formatted_address=address,
                confidence=confidence,
                address_components=address_components
            )
        
        except Exception as e:
            logger.error(f"百度地图地理编码失败: {e}")
            raise
    
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> ReverseGeocodeResponse:
        """百度地图逆地理编码"""
        params = {
            "ak": self.api_key,
            "location": f"{latitude},{longitude}",
            "output": "json",
            "coordtype": "wgs84ll",  # 使用WGS84坐标系
            "extensions_poi": "1"  # 返回POI信息
        }
        
        url = f"{self.base_url}/reverse_geocoding/v3/?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != 0:
                raise Exception(f"百度地图API错误: {data.get('message', '未知错误')}")
            
            result = data.get("result", {})
            formatted_address = result.get("formatted_address", "")
            addressComponent = result.get("addressComponent", {})
            
            # 构建地址组件
            address_components = {
                "country": addressComponent.get("country", ""),
                "province": addressComponent.get("province", ""),
                "city": addressComponent.get("city", ""),
                "district": addressComponent.get("district", ""),
                "street": addressComponent.get("street", ""),
                "street_number": addressComponent.get("street_number", ""),
                "adcode": addressComponent.get("adcode", ""),
                "country_code": addressComponent.get("country_code", ""),
                "direction": addressComponent.get("direction", ""),
                "distance": addressComponent.get("distance", "")
            }
            
            return ReverseGeocodeResponse(
                address=formatted_address,
                formatted_address=formatted_address,
                address_components=address_components,
                confidence=0.85,  # 百度地图逆地理编码置信度
                country=addressComponent.get("country", ""),
                province=addressComponent.get("province", ""),
                city=addressComponent.get("city", ""),
                district=addressComponent.get("district", ""),
                street=addressComponent.get("street", ""),
                street_number=addressComponent.get("street_number", ""),
                postal_code=addressComponent.get("adcode", "")
            )
        
        except Exception as e:
            logger.error(f"百度地图逆地理编码失败: {e}")
            raise