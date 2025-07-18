#!/bin/bash

# 阿里云服务器部署脚本
# 使用方法: ./deploy.sh

set -e

echo "开始部署 Railway-PY 应用..."

# 配置变量
APP_NAME="railway-py"
CONTAINER_NAME="railway-py"
IMAGE_NAME="railway-py:latest"
PORT=8000

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker安装完成，请重新登录后再次运行此脚本"
    exit 1
fi

# 停止并删除现有容器
echo "停止现有容器..."
sudo docker stop $CONTAINER_NAME 2>/dev/null || true
sudo docker rm $CONTAINER_NAME 2>/dev/null || true

# 删除旧镜像
echo "删除旧镜像..."
sudo docker rmi $IMAGE_NAME 2>/dev/null || true

# 构建新镜像
echo "构建Docker镜像..."
sudo docker build -t $IMAGE_NAME .

# 运行新容器
echo "启动新容器..."
sudo docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $PORT:$PORT \
  $IMAGE_NAME

# 检查容器状态
echo "检查容器状态..."
sleep 5
sudo docker ps | grep $CONTAINER_NAME

echo "部署完成！"
echo "应用访问地址: http://localhost:$PORT"
echo "查看日志: sudo docker logs $CONTAINER_NAME"
echo "进入容器: sudo docker exec -it $CONTAINER_NAME /bin/bash"
