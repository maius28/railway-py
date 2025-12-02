# Railway-py 快速启动

## 🚀 一键启动

```bash
# 方式一：使用启动脚本（推荐）
./start.sh start

# 方式二：使用 docker-compose
docker-compose up -d
```

## 🔧 常用命令

```bash
# 查看服务状态
./start.sh status

# 查看日志
./start.sh logs

# 重启服务
./start.sh restart

# 停止服务
./start.sh stop
```

## ✅ 验证服务

- API 文档: <http://localhost:8000/docs>
- 健康检查: `curl http://localhost:8000/health`
- Ping 测试: `curl http://localhost:8000/ping`

## 📚 详细文档

查看完整部署指南: [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)

## ⚠️ 首次启动注意

1. 确保端口 3306 和 8000 未被占用
2. Docker 需要有足够权限和资源
3. 首次启动需要下载镜像，可能需要几分钟

## 🐛 常见问题

### 健康检查失败

```bash
# 查看容器日志
docker-compose logs railway-py

# 手动测试健康检查
curl http://localhost:8000/health
```

### 数据库连接失败

```bash
# 检查 MySQL 状态
docker-compose logs mysql

# 验证数据库连接
docker-compose exec mysql mysql -u railway -pqwe123 -e "SELECT 1;"
```

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000
lsof -i :3306

# 修改 docker-compose.yml 中的端口映射
```
