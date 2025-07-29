"""高德地图地理编码提供商"""

from typing import Optional, Dict, Any
from urllib.parse import urlencode

from app.models.geocoding import GeocodeResponse, ReverseGeocodeResponse
from app.services.providers.base_provider import BaseGeocodingProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AmapProvider(BaseGeocodingProvider):
    """高德地图地理编码提供商"""
    
    def __init__(self, client, settings):
        super().__init__(client, settings)
        self._validate_api_key()
    
    async def geocode(self, address: str, city: Optional[str] = None) -> GeocodeResponse:
        """高德地图地理编码"""
        params = {
            "key": self.api_key,
            "address": address,
            "output": "json"
        }
        
        if city:
            params["city"] = city
        
        url = f"{self.base_url}/geocode/geo?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "1":
                raise Exception(f"高德地图API错误: {data.get('info', '未知错误')}")
            
            geocodes = data.get("geocodes", [])
            if not geocodes:
                raise Exception("未找到地理编码结果")
            
            geocode = geocodes[0]
            location = geocode.get("location", "")
            
            if not location:
                raise Exception("地理编码结果中缺少坐标信息")
            
            lng, lat = map(float, location.split(","))
            
            # 构建地址组件
            address_components = {
                "country": geocode.get("country", ""),
                "province": geocode.get("province", ""),
                "city": geocode.get("city", ""),
                "district": geocode.get("district", ""),
                "township": geocode.get("township", ""),
                "street": geocode.get("street", ""),
                "number": geocode.get("number", ""),
                "adcode": geocode.get("adcode", ""),
                "level": geocode.get("level", "")
            }
            
            # 计算置信度（基于level字段）
            confidence = self._calculate_confidence(geocode.get("level", ""))
            
            return GeocodeResponse(
                latitude=lat,
                longitude=lng,
                formatted_address=geocode.get("formatted_address", address),
                confidence=confidence,
                address_components=address_components
            )
        
        except Exception as e:
            logger.error(f"高德地图地理编码失败: {e}")
            raise
    
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> ReverseGeocodeResponse:
        """高德地图逆地理编码"""
        params = {
            "key": self.api_key,
            "location": f"{longitude},{latitude}",
            "radius": min(radius, 3000),  # 高德地图最大支持3000米
            "extensions": "all",
            "output": "json"
        }
        
        url = f"{self.base_url}/geocode/regeo?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "1":
                raise Exception(f"高德地图API错误: {data.get('info', '未知错误')}")
            
            regeocode = data.get("regeocode", {})
            if not regeocode:
                raise Exception("未找到逆地理编码结果")
            
            formatted_address = regeocode.get("formatted_address", "")
            addressComponent = regeocode.get("addressComponent", {})
            
            # 构建地址组件
            address_components = {
                "country": addressComponent.get("country", ""),
                "province": addressComponent.get("province", ""),
                "city": addressComponent.get("city", ""),
                "district": addressComponent.get("district", ""),
                "township": addressComponent.get("township", ""),
                "street": addressComponent.get("streetNumber", {}).get("street", ""),
                "street_number": addressComponent.get("streetNumber", {}).get("number", ""),
                "adcode": addressComponent.get("adcode", ""),
                "building": addressComponent.get("building", {})
            }
            
            return ReverseGeocodeResponse(
                address=formatted_address,
                formatted_address=formatted_address,
                address_components=address_components,
                confidence=0.9,  # 高德地图逆地理编码通常比较准确
                country=addressComponent.get("country", ""),
                province=addressComponent.get("province", ""),
                city=addressComponent.get("city", ""),
                district=addressComponent.get("district", ""),
                street=addressComponent.get("streetNumber", {}).get("street", ""),
                street_number=addressComponent.get("streetNumber", {}).get("number", ""),
                postal_code=addressComponent.get("adcode", "")
            )
        
        except Exception as e:
            logger.error(f"高德地图逆地理编码失败: {e}")
            raise
    
    def _calculate_confidence(self, level: str) -> float:
        """根据高德地图的level字段计算置信度"""
        level_confidence = {
            "国家": 0.3,
            "省": 0.4,
            "市": 0.5,
            "区县": 0.6,
            "开发区": 0.7,
            "乡镇": 0.7,
            "村庄": 0.8,
            "热点商圈": 0.8,
            "兴趣点": 0.9,
            "门牌号": 0.95,
            "单元号": 0.98
        }
        
        return level_confidence.get(level, 0.7)