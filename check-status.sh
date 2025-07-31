#!/bin/bash

# 服务器状态检查脚本
# 使用方法: ./check-status.sh

echo "========================================="
echo "Railway-PY 应用状态检查"
echo "检查时间: $(date)"
echo "========================================="

# 检查Docker服务
echo "1. 检查Docker服务状态:"
if systemctl is-active --quiet docker; then
    echo "✅ Docker服务正在运行"
    docker --version
else
    echo "❌ Docker服务未运行"
    echo "启动Docker服务: sudo systemctl start docker"
fi

echo ""

# 检查部署目录
echo "2. 检查部署目录:"
if [ -d "/opt/railway-py" ]; then
    echo "✅ 部署目录存在: /opt/railway-py"
    echo "目录内容:"
    ls -la /opt/railway-py
    
    if [ -d "/opt/railway-py/.git" ]; then
        echo "✅ Git仓库存在"
        cd /opt/railway-py
        echo "当前分支: $(git branch --show-current)"
        echo "最新提交: $(git log -1 --oneline)"
    else
        echo "❌ Git仓库不存在"
    fi
else
    echo "❌ 部署目录不存在"
fi

echo ""

# 检查Docker镜像
echo "3. 检查Docker镜像:"
if docker images | grep railway-py; then
    echo "✅ Docker镜像存在"
else
    echo "❌ Docker镜像不存在"
fi

echo ""

# 检查Docker容器
echo "4. 检查Docker容器:"
if docker ps | grep railway-py; then
    echo "✅ 容器正在运行"
    
    # 显示容器详细信息
    echo ""
    echo "容器详细信息:"
    docker inspect railway-py --format='State: {{.State.Status}}, StartedAt: {{.State.StartedAt}}, RestartCount: {{.State.RestartCount}}'
    
    echo ""
    echo "容器端口映射:"
    docker port railway-py
    
    echo ""
    echo "容器日志（最后20行）:"
    docker logs --tail 20 railway-py
    
else
    echo "❌ 容器未在运行"
    
    # 检查是否有停止的容器
    if docker ps -a | grep railway-py; then
        echo "发现停止的容器:"
        docker ps -a | grep railway-py
        
        echo ""
        echo "容器日志（最后20行）:"
        docker logs --tail 20 railway-py
    else
        echo "没有找到任何railway-py容器"
    fi
fi

echo ""

# 检查端口占用
echo "5. 检查端口占用:"
if netstat -tulpn | grep :8000; then
    echo "✅ 端口8000已被占用"
    netstat -tulpn | grep :8000
else
    echo "❌ 端口8000未被占用"
fi

echo ""

# 测试服务
echo "6. 测试服务:"
if curl -f http://localhost:8000/ping 2>/dev/null; then
    echo "✅ 服务响应正常"
    echo "响应内容:"
    curl -s http://localhost:8000/ping
else
    echo "❌ 服务无响应"
fi

echo ""

# 显示系统资源
echo "7. 系统资源状态:"
echo "内存使用:"
free -h
echo ""
echo "磁盘使用:"
df -h /
echo ""
echo "CPU负载:"
uptime

echo ""
echo "========================================="
echo "检查完成"
echo "========================================="
