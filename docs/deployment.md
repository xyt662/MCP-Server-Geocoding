# 部署指南

本文档介绍如何在不同环境中部署 MCP Server Geocoding 服务。

## 目录

- [环境要求](#环境要求)
- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [云服务部署](#云服务部署)
- [生产环境配置](#生产环境配置)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

## 环境要求

### 基础要求

- Python 3.9+
- 内存: 最少 512MB，推荐 1GB+
- 磁盘: 最少 1GB 可用空间
- 网络: 需要访问地理编码API服务

### API密钥

至少需要以下其中一个地理编码服务的API密钥：

- **高德地图**: [申请地址](https://lbs.amap.com/)
- **百度地图**: [申请地址](https://lbsyun.baidu.com/)
- **Google Maps**: [申请地址](https://developers.google.com/maps)

## 本地部署

### 1. 克隆项目

```bash
git clone https://github.com/your-username/MCP-Server-Geocoding.git
cd MCP-Server-Geocoding
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置API密钥
```

### 5. 启动服务

```bash
# 开发模式
python start.py --reload

# 生产模式
python start.py --workers 4
```

## Docker部署

### 单容器部署

```bash
# 构建镜像
docker build -t mcp-geocoding .

# 运行容器
docker run -d \
  --name mcp-geocoding \
  -p 4000:4000 \
  -e AMAP_API_KEY=your_api_key \
  -e GEOCODING_PROVIDER=amap \
  mcp-geocoding
```

### Docker Compose部署

```bash
# 基础部署
docker-compose up -d

# 包含Redis缓存
docker-compose --profile with-redis up -d

# 包含Nginx反向代理
docker-compose --profile with-nginx up -d
```

### 环境变量配置

创建 `.env` 文件：

```env
# API配置
AMAP_API_KEY=your_amap_api_key
BAIDU_API_KEY=your_baidu_api_key
GOOGLE_API_KEY=your_google_api_key

# 服务配置
GEOCODING_PROVIDER=amap
HOST=0.0.0.0
PORT=4000
DEBUG=false

# 性能配置
CACHE_ENABLED=true
CACHE_TTL=3600
RATE_LIMIT_ENABLED=true
```

## 云服务部署

### AWS ECS部署

1. **创建任务定义**

```json
{
  "family": "mcp-geocoding",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "mcp-geocoding",
      "image": "your-account.dkr.ecr.region.amazonaws.com/mcp-geocoding:latest",
      "portMappings": [
        {
          "containerPort": 4000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "GEOCODING_PROVIDER",
          "value": "amap"
        }
      ],
      "secrets": [
        {
          "name": "AMAP_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:mcp-geocoding/api-keys"
        }
      ]
    }
  ]
}
```

2. **创建服务**

```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name mcp-geocoding \
  --task-definition mcp-geocoding \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Google Cloud Run部署

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT-ID/mcp-geocoding

# 部署服务
gcloud run deploy mcp-geocoding \
  --image gcr.io/PROJECT-ID/mcp-geocoding \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEOCODING_PROVIDER=amap \
  --set-secrets AMAP_API_KEY=amap-api-key:latest
```

### Azure Container Instances部署

```bash
az container create \
  --resource-group myResourceGroup \
  --name mcp-geocoding \
  --image your-registry.azurecr.io/mcp-geocoding:latest \
  --cpu 1 \
  --memory 1 \
  --ports 4000 \
  --environment-variables GEOCODING_PROVIDER=amap \
  --secure-environment-variables AMAP_API_KEY=your_api_key
```

## 生产环境配置

### 性能优化

```env
# 工作进程数（通常为CPU核心数）
WORKERS=4

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=10000

# 超时配置
GEOCODING_TIMEOUT=10
GEOCODING_RETRY_TIMES=3

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

### 安全配置

```env
# CORS配置
ALLOWED_ORIGINS=["https://yourdomain.com"]

# 禁用调试模式
DEBUG=false

# 日志级别
LOG_LEVEL=INFO
```

### 负载均衡配置

**Nginx配置示例**:

```nginx
upstream mcp_geocoding {
    server 127.0.0.1:4000;
    server 127.0.0.1:4001;
    server 127.0.0.1:4002;
    server 127.0.0.1:4003;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://mcp_geocoding;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://mcp_geocoding/health;
        access_log off;
    }
}
```

## 监控和日志

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细监控脚本
#!/bin/bash
HEALTH_URL="http://localhost:4000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### 日志配置

```python
# 生产环境日志配置
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
```

### Prometheus监控

```python
# 添加Prometheus指标
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('geocoding_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('geocoding_request_duration_seconds', 'Request duration')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: 高德地图API错误: INVALID_USER_KEY
   解决: 检查API密钥是否正确，是否有足够的配额
   ```

2. **连接超时**
   ```
   错误: httpx.ConnectTimeout
   解决: 检查网络连接，增加超时时间
   ```

3. **内存不足**
   ```
   错误: MemoryError
   解决: 增加内存限制，优化缓存配置
   ```

### 调试命令

```bash
# 检查服务状态
curl -v http://localhost:4000/health

# 查看日志
docker logs mcp-geocoding

# 检查资源使用
docker stats mcp-geocoding

# 测试API
curl -X POST http://localhost:4000/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "北京市朝阳区三里屯"}'
```

### 性能调优

1. **调整工作进程数**
   ```bash
   # 根据CPU核心数调整
   uvicorn app.main:app --workers $(nproc)
   ```

2. **优化缓存配置**
   ```env
   CACHE_TTL=7200  # 增加缓存时间
   CACHE_MAX_SIZE=50000  # 增加缓存大小
   ```

3. **启用连接池**
   ```python
   # 在httpx客户端配置中
   limits = httpx.Limits(
       max_keepalive_connections=100,
       max_connections=200
   )
   ```

## 备份和恢复

### 配置备份

```bash
# 备份配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# 备份到云存储
aws s3 cp config-backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

### 灾难恢复

```bash
# 快速恢复脚本
#!/bin/bash
set -e

echo "开始灾难恢复..."

# 拉取最新镜像
docker pull your-registry/mcp-geocoding:latest

# 停止旧服务
docker-compose down

# 启动新服务
docker-compose up -d

# 等待服务启动
sleep 30

# 健康检查
if curl -f http://localhost:4000/health; then
    echo "服务恢复成功"
else
    echo "服务恢复失败"
    exit 1
fi
```