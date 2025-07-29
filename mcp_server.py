#!/usr/bin/env python3
"""MCP Server for Geocoding Services

基于百度官方MCP服务架构设计的地理编码MCP服务器
支持多提供商（高德、百度、Google Maps）的地理编码和逆地理编码服务
"""

import os
import asyncio
from typing import Dict, Any, List

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from app.config import get_settings
from app.services.geocoding_service import GeocodingService
from app.models.geocoding import GeocodeRequest, ReverseGeocodeRequest
from app.utils.logger import get_logger

# 创建MCP服务器实例
mcp = FastMCP(
    name="mcp-server-geocoding",
    version="1.0.0",
    instructions="高性能地理编码MCP服务，支持多提供商的地理编码和逆地理编码功能。"
)

# 初始化配置和服务
settings = get_settings()
logger = get_logger(__name__)
geocoding_service: GeocodingService = None


async def initialize_service():
    """初始化地理编码服务"""
    global geocoding_service
    try:
        geocoding_service = GeocodingService()
        await geocoding_service.initialize()
        logger.info("MCP地理编码服务初始化完成")
    except Exception as e:
        logger.error(f"MCP地理编码服务初始化失败: {e}")
        raise


async def cleanup_service():
    """清理服务资源"""
    global geocoding_service
    if geocoding_service:
        await geocoding_service.close()
        logger.info("MCP地理编码服务已关闭")


async def geocode_tool(
    name: str, arguments: dict
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """地理编码工具：将地址转换为经纬度坐标"""
    try:
        address = arguments.get("address", "")
        city = arguments.get("city", None)
        
        if not address:
            raise ValueError("地址参数不能为空")
        
        # 验证请求参数
        request = GeocodeRequest(address=address, city=city)
        
        # 调用地理编码服务
        result = await geocoding_service.geocode(request.address, request.city)
        
        # 构建响应
        response_data = {
            "latitude": result.latitude,
            "longitude": result.longitude,
            "formatted_address": result.formatted_address,
            "confidence": result.confidence,
            "address_components": result.address_components
        }
        
        return [types.TextContent(
            type="text", 
            text=f"地理编码成功：{address} -> ({result.latitude}, {result.longitude})\n详细信息：{response_data}"
        )]
        
    except Exception as e:
        logger.error(f"地理编码失败: {e}")
        return [types.TextContent(
            type="text", 
            text=f"地理编码失败: {str(e)}"
        )]


async def reverse_geocode_tool(
    name: str, arguments: dict
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """逆地理编码工具：将经纬度坐标转换为地址信息"""
    try:
        latitude = arguments.get("latitude")
        longitude = arguments.get("longitude")
        radius = arguments.get("radius", 1000)
        
        if latitude is None or longitude is None:
            raise ValueError("纬度和经度参数不能为空")
        
        # 验证请求参数
        request = ReverseGeocodeRequest(
            latitude=float(latitude), 
            longitude=float(longitude), 
            radius=int(radius)
        )
        
        # 调用逆地理编码服务
        result = await geocoding_service.reverse_geocode(
            request.latitude, 
            request.longitude, 
            request.radius
        )
        
        # 构建响应
        response_data = {
            "address": result.address,
            "formatted_address": result.formatted_address,
            "confidence": result.confidence,
            "country": result.country,
            "province": result.province,
            "city": result.city,
            "district": result.district,
            "street": result.street,
            "street_number": result.street_number,
            "address_components": result.address_components
        }
        
        return [types.TextContent(
            type="text", 
            text=f"逆地理编码成功：({request.latitude}, {request.longitude}) -> {result.address}\n详细信息：{response_data}"
        )]
        
    except Exception as e:
        logger.error(f"逆地理编码失败: {e}")
        return [types.TextContent(
            type="text", 
            text=f"逆地理编码失败: {str(e)}"
        )]


async def health_check_tool(
    name: str, arguments: dict
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """健康检查工具"""
    try:
        if not geocoding_service:
            return [types.TextContent(
                type="text", 
                text="服务未初始化"
            )]
        
        is_healthy = await geocoding_service.health_check()
        uptime = geocoding_service.get_uptime()
        cache_stats = geocoding_service.get_cache_stats()
        
        status_info = {
            "status": "healthy" if is_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "provider": settings.GEOCODING_PROVIDER,
            "cache_stats": cache_stats
        }
        
        return [types.TextContent(
            type="text", 
            text=f"服务状态：{status_info}"
        )]
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return [types.TextContent(
            type="text", 
            text=f"健康检查失败: {str(e)}"
        )]


async def list_tools() -> List[types.Tool]:
    """列出所有可用的工具"""
    return [
        types.Tool(
            name="geocode",
            description="地理编码服务：将地址转换为经纬度坐标。支持中文地址和详细的地址组件解析。",
            inputSchema={
                "type": "object",
                "required": ["address"],
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "要进行地理编码的地址，支持结构化地址如'北京市朝阳区三里屯'或地标描述",
                        "minLength": 1,
                        "maxLength": 500
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名称，用于提高编码精度（可选）",
                        "maxLength": 100
                    }
                }
            }
        ),
        types.Tool(
            name="reverse_geocode",
            description="逆地理编码服务：将经纬度坐标转换为详细的地址信息，包括行政区划和POI信息。",
            inputSchema={
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "纬度坐标（WGS84坐标系）",
                        "minimum": -90,
                        "maximum": 90
                    },
                    "longitude": {
                        "type": "number",
                        "description": "经度坐标（WGS84坐标系）",
                        "minimum": -180,
                        "maximum": 180
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径（米），默认1000米",
                        "minimum": 1,
                        "maximum": 50000,
                        "default": 1000
                    }
                }
            }
        ),
        types.Tool(
            name="health_check",
            description="健康检查服务：检查地理编码服务的运行状态、性能指标和缓存统计。",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


async def dispatch(
    name: str, arguments: dict
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """工具调度器：根据工具名称调用对应的处理函数"""
    
    # 确保服务已初始化
    if not geocoding_service:
        await initialize_service()
    
    # 调度到对应的工具函数
    if name == "geocode":
        return await geocode_tool(name, arguments)
    elif name == "reverse_geocode":
        return await reverse_geocode_tool(name, arguments)
    elif name == "health_check":
        return await health_check_tool(name, arguments)
    else:
        raise ValueError(f"未知的工具: {name}")


# 注册MCP服务器的处理函数
mcp._mcp_server.list_tools()(list_tools)
mcp._mcp_server.call_tool()(dispatch)


async def main():
    """主函数"""
    try:
        # 初始化服务
        await initialize_service()
        
        # 运行MCP服务器
        logger.info("启动MCP地理编码服务器...")
        await mcp.run_async()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"MCP服务器运行错误: {e}")
        raise
    finally:
        # 清理资源
        await cleanup_service()


if __name__ == "__main__":
    # 同步运行入口（兼容mcp.run()）
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")
        exit(1)