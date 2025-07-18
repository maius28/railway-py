#!/bin/bash

# 本地部署脚本 - 用于在阿里云服务器上手动部署
# 使用方法: 将此脚本上传到服务器并执行

set -e

echo "开始部署 Railway-PY 应用..."

# 配置变量
APP_NAME="railway-py"
CONTAINER_NAME="railway-py"
IMAGE_NAME="railway-py:latest"
PORT=8000
REPO_URL="https://github.com/maius28/railway-py.git"
DEPLOY_DIR="/opt/railway-py"

# 进入部署目录
cd $DEPLOY_DIR || { echo "目录不存在，正在创建..."; mkdir -p $DEPLOY_DIR; cd $DEPLOY_DIR; }

# 如果是第一次部署，克隆代码
if [ ! -d ".git" ]; then
    echo "第一次部署，正在克隆代码..."
    git clone $REPO_URL .
else
    echo "更新代码..."
    git fetch origin
    git reset --hard origin/master
fi

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
sleep 10

# 检查容器状态
echo "检查容器状态..."
docker ps | grep $CONTAINER_NAME

# 测试服务
echo "测试服务..."
curl -f http://localhost:$PORT/ping && echo "✅ 服务启动成功！" || echo "❌ 服务启动失败"

# 清理Docker系统（可选）
echo "清理Docker系统..."
docker system prune -f

echo "部署完成！"
echo "应用访问地址: http://服务器IP:$PORT"
echo "API文档地址: http://服务器IP:$PORT/docs"
echo "查看日志: docker logs $CONTAINER_NAME"
echo "进入容器: docker exec -it $CONTAINER_NAME /bin/bash"
