"""地理编码相关数据模型"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class GeocodeRequest(BaseModel):
    """地理编码请求模型"""
    address: str = Field(..., description="要编码的地址", min_length=1, max_length=500)
    city: Optional[str] = Field(None, description="城市名称，用于提高编码精度")
    
    @validator('address')
    def validate_address(cls, v):
        if not v or not v.strip():
            raise ValueError('地址不能为空')
        return v.strip()


class GeocodeResponse(BaseModel):
    """地理编码响应模型"""
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    formatted_address: str = Field(..., description="格式化后的地址")
    confidence: Optional[float] = Field(None, description="置信度 (0-1)")
    address_components: Optional[Dict[str, Any]] = Field(None, description="地址组件")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('纬度必须在-90到90之间')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('经度必须在-180到180之间')
        return v


class ReverseGeocodeRequest(BaseModel):
    """逆地理编码请求模型"""
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    radius: Optional[int] = Field(1000, description="搜索半径（米）", ge=1, le=50000)
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('纬度必须在-90到90之间')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('经度必须在-180到180之间')
        return v


class ReverseGeocodeResponse(BaseModel):
    """逆地理编码响应模型"""
    address: str = Field(..., description="地址")
    formatted_address: str = Field(..., description="格式化后的地址")
    address_components: Optional[Dict[str, Any]] = Field(None, description="地址组件")
    confidence: Optional[float] = Field(None, description="置信度 (0-1)")
    
    # 详细地址组件
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    district: Optional[str] = Field(None, description="区县")
    street: Optional[str] = Field(None, description="街道")
    street_number: Optional[str] = Field(None, description="门牌号")
    postal_code: Optional[str] = Field(None, description="邮政编码")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: Optional[str] = Field(None, description="错误时间")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    timestamp: float = Field(..., description="检查时间戳")
    service: str = Field(..., description="服务名称")
    version: Optional[str] = Field(None, description="服务版本")
    uptime: Optional[float] = Field(None, description="运行时间（秒）")