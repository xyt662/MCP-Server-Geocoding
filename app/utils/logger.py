"""日志工具模块"""

import logging
import sys
from typing import Optional

from app.config import get_settings

settings = get_settings()

# 全局日志配置
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器"""
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(settings.LOG_FORMAT)
        )
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    return logger


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, logger_name: str = "request"):
        self.logger = get_logger(logger_name)
    
    def log_request(self, method: str, url: str, params: dict = None, headers: dict = None):
        """记录请求日志"""
        self.logger.info(f"请求: {method} {url}")
        if params:
            # 隐藏敏感信息
            safe_params = self._sanitize_params(params)
            self.logger.debug(f"参数: {safe_params}")
    
    def log_response(self, status_code: int, response_time: float, response_size: int = None):
        """记录响应日志"""
        self.logger.info(f"响应: {status_code} ({response_time:.3f}s)")
        if response_size:
            self.logger.debug(f"响应大小: {response_size} bytes")
    
    def log_error(self, error: Exception, context: dict = None):
        """记录错误日志"""
        self.logger.error(f"错误: {error}", exc_info=True)
        if context:
            self.logger.error(f"上下文: {context}")
    
    def _sanitize_params(self, params: dict) -> dict:
        """清理敏感参数"""
        sensitive_keys = {'key', 'ak', 'api_key', 'token', 'password', 'secret'}
        sanitized = {}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized