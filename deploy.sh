#!/bin/bash

# 手动部署脚本 - 用于在阿里云服务器上手动部署
# 使用方法: 
# 1. 将代码上传到服务器 /opt/railway-py 目录
# 2. 运行此脚本: ./deploy.sh

set -e

echo "开始部署 Railway-PY 应用..."

# 配置变量
APP_NAME="railway-py"
CONTAINER_NAME="railway-py"
IMAGE_NAME="railway-py:latest"
PORT=8000
DEPLOY_DIR="/opt/railway-py"

# 检查是否在正确目录
if [ ! -f "Dockerfile" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ 请确保在项目根目录运行此脚本（包含Dockerfile和requirements.txt）"
    exit 1
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker服务未运行，请启动Docker服务"
    echo "运行: sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker状态正常"

# 停止并删除现有容器
echo "停止现有容器..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 删除旧镜像（可选，节省空间）
echo "删除旧镜像..."
docker rmi $IMAGE_NAME 2>/dev/null || true

# 构建新镜像
echo "构建Docker镜像..."
docker build -t $IMAGE_NAME .

# 运行新容器
echo "启动新容器..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $PORT:$PORT \
  $IMAGE_NAME

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查容器状态
echo "检查容器状态..."
if docker ps | grep $CONTAINER_NAME > /dev/null; then
    echo "✅ 容器运行正常"
    docker ps | grep $CONTAINER_NAME
else
    echo "❌ 容器启动失败"
    echo "容器日志："
    docker logs $CONTAINER_NAME
    exit 1
fi

# 测试服务
echo "测试服务..."
for i in {1..5}; do
    if curl -f http://localhost:$PORT/ping 2>/dev/null; then
        echo "✅ 服务响应正常"
        break
    else
        echo "⏳ 第${i}次测试失败，等待重试..."
        sleep 5
    fi
done

echo "========================================="
echo "部署完成！"
echo "应用访问地址: http://服务器IP:$PORT"
echo "API文档地址: http://服务器IP:$PORT/docs"
echo "查看日志: docker logs $CONTAINER_NAME"
echo "进入容器: docker exec -it $CONTAINER_NAME /bin/bash"
echo "========================================="

# 显示最终状态
echo "最终状态："
echo "容器状态:"
docker ps | grep $CONTAINER_NAME
echo "容器日志（最后10行）:"
docker logs --tail 10 $CONTAINER_NAME
