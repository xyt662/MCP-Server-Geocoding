"""FastAPI主应用文件"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.models.geocoding import GeocodeRequest, GeocodeResponse, ReverseGeocodeRequest, ReverseGeocodeResponse
from app.services.geocoding_service import GeocodingService
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 全局服务实例
geocoding_service: GeocodingService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global geocoding_service
    
    # 启动时初始化服务
    logger.info("正在启动地理编码服务...")
    geocoding_service = GeocodingService()
    await geocoding_service.initialize()
    logger.info("地理编码服务启动完成")
    
    yield
    
    # 关闭时清理资源
    logger.info("正在关闭地理编码服务...")
    if geocoding_service:
        await geocoding_service.close()
    logger.info("地理编码服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MCP Server Geocoding",
    description="高性能地理编码微服务，为AI Agent提供精准的地理位置信息处理能力",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_geocoding_service() -> GeocodingService:
    """获取地理编码服务实例"""
    if geocoding_service is None:
        raise HTTPException(status_code=503, detail="地理编码服务未初始化")
    return geocoding_service


@app.get("/")
async def root() -> Dict[str, Any]:
    """根路径"""
    return {
        "message": "MCP Server Geocoding API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    try:
        service = get_geocoding_service()
        is_healthy = await service.health_check()
        
        if is_healthy:
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "service": "geocoding"
            }
        else:
            raise HTTPException(status_code=503, detail="服务不健康")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="健康检查失败")


@app.post("/geocode", response_model=GeocodeResponse)
async def geocode(
    request: GeocodeRequest,
    service: GeocodingService = Depends(get_geocoding_service)
) -> GeocodeResponse:
    """地理编码：将地址转换为经纬度坐标"""
    try:
        logger.info(f"地理编码请求: {request.address}")
        result = await service.geocode(request.address)
        logger.info(f"地理编码成功: {request.address} -> {result.latitude}, {result.longitude}")
        return result
    except Exception as e:
        logger.error(f"地理编码失败: {request.address}, 错误: {e}")
        raise HTTPException(status_code=400, detail=f"地理编码失败: {str(e)}")


@app.post("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(
    request: ReverseGeocodeRequest,
    service: GeocodingService = Depends(get_geocoding_service)
) -> ReverseGeocodeResponse:
    """逆地理编码：将经纬度坐标转换为地址信息"""
    try:
        logger.info(f"逆地理编码请求: {request.latitude}, {request.longitude}")
        result = await service.reverse_geocode(request.latitude, request.longitude)
        logger.info(f"逆地理编码成功: {request.latitude}, {request.longitude} -> {result.address}")
        return result
    except Exception as e:
        logger.error(f"逆地理编码失败: {request.latitude}, {request.longitude}, 错误: {e}")
        raise HTTPException(status_code=400, detail=f"逆地理编码失败: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )