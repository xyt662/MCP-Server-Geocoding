# MCP Server Geocoding

一个基于 FastAPI 的高性能地理编码微服务，专为 AI Agent 设计，提供精准的地理位置信息处理能力

## 概述

本项目为赋能 AI Agent 精准处理真实世界地理位置信息而开发，作为 MCP (Model Context Protocol) 框架的关键工具，为下游的路径规划、POI 检索等复杂任务奠定基础

## 技术特性

- 🚀 **高性能**: 基于 FastAPI 与 Python 异步编程 (asyncio/httpx) 构建
- 🔄 **双向编码**: 支持地理编码与逆地理编码
- 🛡️ **健壮性**: 多层级错误处理机制
- 🐳 **容器化**: Docker 支持，便于部署
- 📊 **监控**: 内置健康检查和性能监控

## 核心功能

### 🌐 FastAPI REST服务

#### 地理编码 (Geocoding)
将地址文本转换为经纬度坐标

```bash
POST /geocode
{
  "address": "北京市朝阳区三里屯"
}
```

#### 逆地理编码 (Reverse Geocoding)
将经纬度坐标转换为地址信息

```bash
POST /reverse-geocode
{
  "latitude": 39.9042,
  "longitude": 116.4074
}
```

### 🔌 MCP服务器支持

本项目同时提供 **Model Context Protocol (MCP)** 服务器实现，可直接集成到支持MCP的AI应用中：

#### MCP工具
- `geocode`: 地理编码工具
- `reverse_geocode`: 逆地理编码工具  
- `health_check`: 服务健康检查工具

#### MCP服务器启动
```bash
# 启动MCP服务器
python mcp_server.py

# 或使用配置文件
python mcp_server.py --config mcp_config.json
```

## 快速开始

### 本地开发

1. 克隆项目
```bash
git clone https://github.com/xyt662/MCP-Server-Geocoding.git
cd MCP-Server-Geocoding
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

### Docker 部署

```bash
# 构建镜像
docker build -t mcp-geocoding .

# 运行容器
docker run -p 4000:4000 mcp-geocoding
```

### Docker Compose

```bash
docker-compose up -d
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:4000/docs
- ReDoc: http://localhost:4000/redoc

## 项目结构

```
MCP-Server-Geocoding/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   ├── utils/               # 工具函数
│   └── config.py            # 配置管理
├── tests/                   # 测试文件
├── docker/                  # Docker 相关文件
├── docs/                    # 文档
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
└── README.md               # 项目说明
```

## 配置

环境变量配置:

```bash
# 服务配置
HOST=0.0.0.0
PORT=4000
DEBUG=false

# 地理编码服务配置
GEOCODING_API_KEY=your_api_key
GEOCODING_PROVIDER=amap  # 支持: amap, baidu, google
```

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目链接: [https://github.com/xyt662/MCP-Server-Geocoding](https://github.com/xyt662/MCP-Server-Geocoding)
- 问题反馈: [Issues](https://github.com/xyt662/MCP-Server-Geocoding/issues)
