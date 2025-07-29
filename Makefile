.PHONY: help install test lint format clean dev build docker-build docker-run docker-stop mcp-dev mcp-test

# 默认目标
help:
	@echo "MCP Server Geocoding - 可用命令:"
	@echo "  install     - 安装依赖"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理缓存文件"
	@echo "  dev         - 启动FastAPI开发服务器"
	@echo "  mcp-dev     - 启动MCP开发服务器"
	@echo "  mcp-test    - 测试MCP客户端示例"
	@echo "  build       - 构建项目"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run  - 运行Docker容器"
	@echo "  docker-stop - 停止Docker容器"

# 安装依赖
install:
	pip install -r requirements.txt

# 运行测试
test:
	pytest -v --cov=app --cov-report=term-missing

# 代码检查
lint:
	flake8 app tests
	isort --check-only app tests
	black --check app tests
	mypy app --ignore-missing-imports

# 代码格式化
format:
	isort app tests
	black app tests

# 清理缓存文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

# 启动FastAPI开发服务器
dev:
	@echo "启动开发服务器..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 4000

# 启动MCP开发服务器
mcp-dev:
	python mcp_server.py

# 测试MCP客户端示例
mcp-test:
	python examples/mcp_client_example.py

# 构建项目
build: clean lint test
	@echo "项目构建完成"

# 构建Docker镜像
docker-build:
	docker build -t mcp-geocoding .

# 运行Docker容器
docker-run:
	@echo "运行Docker容器..."
	docker run -p 4000:4000 --env-file .env mcp-geocoding

# 停止Docker容器
docker-stop:
	docker stop mcp-geocoding-container || true
	docker rm mcp-geocoding-container || true

# 使用Docker Compose启动
docker-compose-up:
	docker-compose up -d

# 使用Docker Compose停止
docker-compose-down:
	docker-compose down

# 安装开发依赖
install-dev: install
	pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# 运行完整的CI检查
ci: install-dev lint test
	@echo "CI检查完成"

# 生成API文档
docs:
	@echo "启动文档服务器..."
	python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"
	python start.py

# 检查安全漏洞
security:
	pip install safety bandit
	safety check
	bandit -r app/

# 更新依赖
update:
	pip list --outdated
	@echo "请手动更新requirements.txt中的版本号"