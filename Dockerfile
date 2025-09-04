# Docker配置文件
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建必要的目录
RUN mkdir -p /app/data/raw \
    /app/data/processed \
    /app/data/embeddings \
    /app/data/indices \
    /app/models/pretrained \
    /app/models/finetuned \
    /app/logs/app \
    /app/logs/access \
    /app/logs/error

# 设置权限
RUN chmod +x /app/src/main.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "src/main.py"]