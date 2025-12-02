#!/bin/bash

# Railway-py Docker 快速启动脚本
# 使用方法: ./start.sh [start|stop|restart|logs|status]

set -e

COMMAND=${1:-start}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
}

# 检查必要文件
check_files() {
    if [ ! -f "docker compose.yml" ]; then
        print_error "找不到 docker compose.yml 文件"
        exit 1
    fi
}

# 创建必要目录
create_dirs() {
    print_info "创建必要目录..."
    mkdir -p logs
    chmod 755 logs
}

# 启动服务
start_service() {
    print_info "启动 Railway-py 服务..."
    docker compose up --build -d
    
    print_info "等待服务启动..."
    sleep 5
    
    print_info "检查服务状态..."
    docker compose ps
    
    echo ""
    print_info "服务已启动！"
    print_info "API 文档: http://localhost:8000/docs"
    print_info "健康检查: http://localhost:8000/health"
    print_info "查看日志: ./start.sh logs"
}

# 停止服务
stop_service() {
    print_info "停止 Railway-py 服务..."
    docker compose down
    print_info "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启 Railway-py 服务..."
    docker compose restart
    sleep 5
    docker compose ps
    print_info "服务已重启"
}

# 查看日志
view_logs() {
    print_info "查看服务日志 (Ctrl+C 退出)..."
    docker compose logs -f --tail=100
}

# 查看状态
check_status() {
    print_info "服务状态:"
    docker compose ps
    
    echo ""
    print_info "容器资源使用:"
    docker stats --no-stream $(docker compose ps -q)
    
    echo ""
    print_info "测试 API 连接..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_info "✓ API 服务正常"
        curl -s http://localhost:8000/health | python3 -m json.tool
    else
        print_warn "✗ API 服务无响应"
    fi
}

# 清理环境
cleanup() {
    print_warn "此操作将删除所有容器和数据卷！"
    read -p "确认继续？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "清理环境..."
        docker compose down -v
        print_info "清理完成"
    else
        print_info "操作已取消"
    fi
}

# 主逻辑
main() {
    check_docker
    check_files
    
    case "$COMMAND" in
        start)
            create_dirs
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        logs)
            view_logs
            ;;
        status)
            check_status
            ;;
        clean)
            cleanup
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|logs|status|clean}"
            echo ""
            echo "命令说明:"
            echo "  start   - 构建并启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  logs    - 查看实时日志"
            echo "  status  - 查看服务状态"
            echo "  clean   - 清理环境（删除数据）"
            exit 1
            ;;
    esac
}

main
