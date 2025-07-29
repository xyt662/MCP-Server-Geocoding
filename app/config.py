"""应用配置管理"""

import os
from typing import List
from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=4000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"], 
        env="ALLOWED_ORIGINS"
    )
    
    # 地理编码服务配置
    GEOCODING_PROVIDER: str = Field(default="amap", env="GEOCODING_PROVIDER")
    GEOCODING_API_KEY: str = Field(default="", env="GEOCODING_API_KEY")
    GEOCODING_TIMEOUT: int = Field(default=10, env="GEOCODING_TIMEOUT")
    GEOCODING_RETRY_TIMES: int = Field(default=3, env="GEOCODING_RETRY_TIMES")
    
    # 高德地图配置
    AMAP_API_KEY: str = Field(default="", env="AMAP_API_KEY")
    AMAP_BASE_URL: str = Field(
        default="https://restapi.amap.com/v3",
        env="AMAP_BASE_URL"
    )
    
    # 百度地图配置
    BAIDU_API_KEY: str = Field(default="", env="BAIDU_API_KEY")
    BAIDU_BASE_URL: str = Field(
        default="https://api.map.baidu.com",
        env="BAIDU_BASE_URL"
    )
    
    # Google Maps配置
    GOOGLE_API_KEY: str = Field(default="", env="GOOGLE_API_KEY")
    GOOGLE_BASE_URL: str = Field(
        default="https://maps.googleapis.com/maps/api",
        env="GOOGLE_BASE_URL"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # 缓存配置
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 缓存时间（秒）
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # 时间窗口（秒）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_api_key(self) -> str:
        """根据提供商获取API密钥"""
        if self.GEOCODING_PROVIDER.lower() == "amap":
            return self.AMAP_API_KEY or self.GEOCODING_API_KEY
        elif self.GEOCODING_PROVIDER.lower() == "baidu":
            return self.BAIDU_API_KEY or self.GEOCODING_API_KEY
        elif self.GEOCODING_PROVIDER.lower() == "google":
            return self.GOOGLE_API_KEY or self.GEOCODING_API_KEY
        else:
            return self.GEOCODING_API_KEY
    
    def get_base_url(self) -> str:
        """根据提供商获取基础URL"""
        if self.GEOCODING_PROVIDER.lower() == "amap":
            return self.AMAP_BASE_URL
        elif self.GEOCODING_PROVIDER.lower() == "baidu":
            return self.BAIDU_BASE_URL
        elif self.GEOCODING_PROVIDER.lower() == "google":
            return self.GOOGLE_BASE_URL
        else:
            raise ValueError(f"不支持的地理编码提供商: {self.GEOCODING_PROVIDER}")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()