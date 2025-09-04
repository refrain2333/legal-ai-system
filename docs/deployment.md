# 法智导航系统 - 部署指南

## 📋 部署概览

本文档详细介绍法智导航系统的部署方法，包括开发环境、测试环境和生产环境的完整部署流程。

### 支持的部署方式
- **本地开发部署**: 开发和调试
- **Docker容器部署**: 标准化部署
- **云服务器部署**: 生产环境
- **Kubernetes部署**: 大规模集群（未来版本）

---

## 🛠️ 环境准备

### 系统要求

**最小配置**:
- CPU: 2核心
- 内存: 4GB RAM
- 存储: 20GB 可用空间
- 系统: Windows 10/Ubuntu 18.04+/CentOS 7+

**推荐配置**:
- CPU: 4核心或更多
- 内存: 8GB RAM或更多
- 存储: 50GB+ SSD
- GPU: NVIDIA GPU (可选，用于模型训练)

### 软件依赖

**必需组件**:
- Python 3.9+
- Git
- Docker (推荐)

**可选组件**:
- NVIDIA Docker (GPU支持)
- Redis (缓存)
- Nginx (反向代理)

---

## 🏠 本地开发部署

### 1. 代码获取

```bash
# 克隆项目（如果使用Git）
git clone <repository-url>
cd 法律指导

# 或直接使用现有项目目录
cd "C:\Users\lenovo\Desktop\法律\指导"
```

### 2. Python环境设置

**Windows环境**:
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 升级pip
python -m pip install --upgrade pip
```

**Linux/Mac环境**:
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 3. 依赖安装

```bash
# 安装Python依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch; import transformers; print('依赖安装成功')"
```

### 4. 配置文件设置

```bash
# 复制配置模板
cp config/config.yaml config/local_config.yaml

# 根据需要修改配置
# 编辑 config/local_config.yaml
```

**关键配置项**:
```yaml
# config/local_config.yaml
data:
  raw_data_dir: "./data/raw"
  processed_data_dir: "./data/processed"

model:
  pretrained_model_name: "shibing624/text2vec-base-chinese"
  
api:
  host: "127.0.0.1"
  port: 8000
  debug: true
  
logging:
  level: "DEBUG"
  log_file: "./logs/dev.log"
```

### 5. 数据准备

```bash
# 创建数据目录
mkdir -p data/raw data/processed

# 放置数据文件（手动操作）
# 将以下文件放入 data/raw/ 目录:
# - raw_laws(1).csv
# - raw_cases(1).csv  
# - 精确映射表.csv
```

### 6. 启动开发服务

```bash
# 进入源码目录
cd src

# 启动API服务
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# 或使用配置文件启动
python -m uvicorn api.main:app --reload --config ../config/local_config.yaml
```

### 7. 验证部署

```bash
# 检查服务状态
curl http://127.0.0.1:8000/health

# 查看API文档
# 浏览器打开: http://127.0.0.1:8000/docs
```

---

## 🐳 Docker容器部署

### 1. Docker环境准备

**安装Docker**:
```bash
# Ubuntu
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Windows: 下载并安装Docker Desktop
# Mac: 下载并安装Docker Desktop

# 验证安装
docker --version
docker-compose --version
```

### 2. 构建镜像

```bash
# 构建应用镜像
docker build -t legal-ai:latest .

# 查看镜像
docker images legal-ai
```

### 3. 单容器运行

```bash
# 运行容器
docker run -d \
  --name legal-ai-app \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  -e LOG_LEVEL=INFO \
  legal-ai:latest

# 查看容器状态
docker ps

# 查看日志
docker logs legal-ai-app
```

### 4. Docker Compose部署

**创建docker-compose.yml**:
```yaml
version: '3.8'

services:
  legal-ai:
    build: .
    container_name: legal-ai-app
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models  
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - LOG_LEVEL=INFO
      - CONFIG_PATH=/app/config/config.yaml
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: legal-ai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - legal-ai
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: legal-ai-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

**启动服务栈**:
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f legal-ai
```

### 5. Nginx配置

**nginx/nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream legal_ai {
        server legal-ai:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API路由
        location /api/ {
            proxy_pass http://legal_ai;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 健康检查
        location /health {
            proxy_pass http://legal_ai/health;
        }

        # 根路径
        location / {
            proxy_pass http://legal_ai;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

## ☁️ 云服务器部署

### 1. 服务器选择

**推荐配置**:
- **阿里云**: ECS实例，4核8GB，Ubuntu 20.04
- **腾讯云**: CVM实例，4核8GB，CentOS 8
- **华为云**: ECS实例，4核8GB，Ubuntu 20.04

### 2. 服务器初始化

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础工具
sudo apt-get install -y git curl wget vim htop

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 代码部署

```bash
# 创建项目目录
sudo mkdir -p /opt/legal-ai
sudo chown $USER:$USER /opt/legal-ai
cd /opt/legal-ai

# 上传代码（多种方式）
# 方式1: Git克隆
git clone <your-repository> .

# 方式2: SCP传输
# scp -r ./local-project user@server:/opt/legal-ai/

# 方式3: rsync同步
# rsync -avz ./local-project/ user@server:/opt/legal-ai/
```

### 4. 环境配置

```bash
# 创建生产配置
cp config/config.yaml config/production.yaml

# 编辑生产配置
vim config/production.yaml
```

**生产环境配置**:
```yaml
# config/production.yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  workers: 4

logging:
  level: "INFO"
  log_file: "/var/log/legal-ai/app.log"

performance:
  api_response_threshold: 1.0
  monitor_cpu: true
  monitor_memory: true
```

### 5. SSL证书配置

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6. 系统服务配置

**创建systemd服务**:
```bash
sudo vim /etc/systemd/system/legal-ai.service
```

**legal-ai.service**:
```ini
[Unit]
Description=Legal AI Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/legal-ai
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=legal-ai
Group=legal-ai

[Install]
WantedBy=multi-user.target
```

**启用服务**:
```bash
# 创建用户
sudo useradd -r -s /bin/false legal-ai
sudo chown -R legal-ai:legal-ai /opt/legal-ai

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable legal-ai
sudo systemctl start legal-ai

# 检查状态
sudo systemctl status legal-ai
```

### 7. 防火墙配置

```bash
# UFW防火墙配置
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 或者iptables配置
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

---

## 📊 监控和日志

### 1. 日志管理

**日志聚合**:
```bash
# 安装logrotate
sudo apt-get install logrotate

# 配置日志轮转
sudo vim /etc/logrotate.d/legal-ai
```

**logrotate配置**:
```
/var/log/legal-ai/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 legal-ai legal-ai
    postrotate
        docker-compose -f /opt/legal-ai/docker-compose.yml restart legal-ai
    endscript
}
```

### 2. 性能监控

**安装监控工具**:
```bash
# 安装Prometheus和Grafana (可选)
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz

# 或使用Docker版本
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 3. 健康检查

**健康检查脚本**:
```bash
#!/bin/bash
# scripts/health_check.sh

API_URL="http://localhost:8000/health"
LOG_FILE="/var/log/legal-ai/health.log"

response=$(curl -s -w "%{http_code}" "$API_URL" -o /dev/null)

if [ "$response" -eq 200 ]; then
    echo "$(date): API健康检查通过" >> "$LOG_FILE"
else
    echo "$(date): API健康检查失败，状态码: $response" >> "$LOG_FILE"
    # 发送告警 (邮件/钉钉/企业微信)
    python3 /opt/legal-ai/scripts/send_alert.py "API服务异常"
fi
```

**设置定时检查**:
```bash
# 添加到crontab
crontab -e
# */5 * * * * /opt/legal-ai/scripts/health_check.sh
```

---

## 🚀 自动化部署

### 1. 部署脚本

**deploy.sh**:
```bash
#!/bin/bash
set -e

echo "开始部署法智导航系统..."

# 变量定义
PROJECT_DIR="/opt/legal-ai"
BACKUP_DIR="/opt/backups/legal-ai-$(date +%Y%m%d-%H%M%S)"
CONFIG_FILE="config/production.yaml"

# 创建备份
echo "创建备份..."
sudo mkdir -p /opt/backups
sudo cp -r $PROJECT_DIR $BACKUP_DIR

# 更新代码
echo "更新代码..."
cd $PROJECT_DIR
git pull origin main

# 构建镜像
echo "构建Docker镜像..."
docker-compose build --no-cache

# 重启服务
echo "重启服务..."
docker-compose down
docker-compose up -d

# 健康检查
echo "等待服务启动..."
sleep 30

# 验证部署
response=$(curl -s -w "%{http_code}" "http://localhost:8000/health" -o /dev/null)
if [ "$response" -eq 200 ]; then
    echo "✅ 部署成功！服务运行正常"
else
    echo "❌ 部署可能有问题，健康检查失败"
    echo "正在回滚到之前版本..."
    
    # 回滚
    docker-compose down
    sudo rm -rf $PROJECT_DIR
    sudo cp -r $BACKUP_DIR $PROJECT_DIR
    cd $PROJECT_DIR
    docker-compose up -d
    
    echo "回滚完成"
    exit 1
fi

echo "🎉 部署完成！"
```

### 2. CI/CD集成

**GitHub Actions示例**:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/legal-ai
          ./deploy.sh
```

---

## 🔧 故障排除

### 常见问题

**1. 端口占用**
```bash
# 查看端口占用
sudo netstat -tlnp | grep :8000

# 杀死占用进程
sudo kill -9 <PID>
```

**2. Docker容器无法启动**
```bash
# 查看容器日志
docker logs legal-ai-app

# 检查容器状态
docker inspect legal-ai-app
```

**3. 内存不足**
```bash
# 查看内存使用
free -h
docker stats

# 清理Docker镜像
docker system prune -af
```

**4. 模型加载失败**
```bash
# 检查模型文件
ls -la models/

# 重新下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('shibing624/text2vec-base-chinese')"
```

### 日志分析

```bash
# API访问日志
tail -f logs/api.log

# 错误日志
grep ERROR logs/api.log

# 性能日志
grep "execution_time" logs/api.log | tail -20
```

---

## 📋 部署检查清单

### 部署前检查
- [ ] 服务器配置满足最低要求
- [ ] 所有依赖软件已安装
- [ ] 数据文件已准备就绪
- [ ] 配置文件已正确设置
- [ ] SSL证书已配置（生产环境）

### 部署后验证
- [ ] API健康检查通过
- [ ] 搜索功能正常工作
- [ ] 响应时间符合要求
- [ ] 日志记录正常
- [ ] 监控告警正常

### 性能测试
- [ ] 并发测试通过
- [ ] 压力测试通过
- [ ] 内存泄漏检查
- [ ] 长时间运行稳定性

---

**📞 技术支持**: 如部署过程中遇到问题，请参考故障排除部分或联系技术支持团队。