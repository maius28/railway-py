# Docker Compose 部署指南

## 📋 配置检查报告

### ✅ 配置优点

1. **服务依赖管理良好**
   - 使用 `depends_on` + `healthcheck` 确保 MySQL 就绪后才启动应用
   - healthcheck 配置合理，有足够的启动时间和重试机制

2. **环境变量配置规范**
   - 数据库配置通过环境变量传递，便于不同环境部署
   - Python 应用正确读取环境变量

3. **数据持久化**
   - MySQL 数据通过 volume 持久化
   - 初始化脚本自动执行

4. **网络隔离**
   - 服务在同一网络中，通过服务名通信

### ⚠️  配置问题及建议

#### 1. **健康检查端点缺失** (严重)
**问题**: `docker-compose.yml` 中 railway-py 服务的 healthcheck 使用 `/health` 端点，但应用中未定义该端点。

**影响**: 健康检查会失败，容器可能被标记为不健康。

**建议修复**:

```python
# 在 app/main.py 中添加 /health 端点
@app.get("/health")
def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        if db_connection.is_connected():
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

#### 2. **安全性问题** (中等)
**问题**: 
- 数据库密码较弱 (`qwe123`)
- root 密码与普通用户密码相同
- 密码直接写在配置文件中

**建议**:
- 使用强密码
- 使用 `.env` 文件管理敏感信息
- 将 `docker-compose.yml` 改为使用环境变量

#### 3. **缺少 .dockerignore** (次要)
**建议**: 创建 `.dockerignore` 文件排除不必要的文件:
```
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
*.md
.env
.venv
venv/
logs/
*.log
.DS_Store
```

#### 4. **requirements.txt 格式问题** (次要)
**问题**: PyTorch CPU 版本的安装语法不规范

**建议修复**:
```txt
fastapi==0.110.2
uvicorn==0.29.0
pydantic>=2.0
numpy==1.26.4
ujson==5.10.0
pymysql==1.1.1
torch==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu
```

#### 5. **日志目录权限** (次要)
**问题**: 容器可能没有权限写入 `./logs` 目录

**建议**: 启动前创建日志目录并设置权限

#### 6. **MySQL 8.0 认证插件** (信息)
**说明**: 已正确配置 `mysql_native_password`，兼容 PyMySQL

---

## 🚀 启动步骤

### 前置要求

- Docker 已安装 (版本 20.10+)
- Docker Compose 已安装 (版本 2.0+)
- 系统内存至少 2GB 可用

### 第一次启动

#### 1. 修复健康检查端点

编辑 `app/main.py`，添加 `/health` 端点:

```python
@app.get("/health")
def health_check():
    """健康检查端点"""
    try:
        if db_connection.is_connected():
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

#### 2. 创建必要目录

```bash
# 创建日志目录
mkdir -p logs

# 设置权限（如果需要）
chmod 755 logs
```

#### 3. 构建并启动服务

```bash
# 构建镜像并启动服务（首次启动）
docker-compose up --build -d

# 查看启动日志
docker-compose logs -f
```

#### 4. 验证服务状态

```bash
# 检查容器状态
docker-compose ps

# 应该看到两个容器都是 healthy 状态
# NAME                IMAGE               STATUS
# railway-mysql       mysql:8.0          Up (healthy)
# server              railway-py         Up (healthy)
```

#### 5. 测试 API

```bash
# 测试 ping 端点
curl http://localhost:8000/ping

# 测试健康检查端点
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/docs
```

---

## 📝 常用命令

### 启动和停止

```bash
# 启动服务（后台运行）
docker-compose up -d

# 停止服务
docker-compose down

# 停止服务并删除数据卷（⚠️ 会删除数据库数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 重启单个服务
docker-compose restart railway-py
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 实时查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs railway-py
docker-compose logs mysql

# 查看最近 100 行日志
docker-compose logs --tail=100 railway-py
```

### 调试和维护

```bash
# 进入容器 shell
docker-compose exec railway-py bash
docker-compose exec mysql bash

# 在容器中执行命令
docker-compose exec railway-py python --version

# 查看容器资源使用情况
docker stats

# 重新构建镜像（代码有更新时）
docker-compose build railway-py
docker-compose up -d railway-py
```

### 数据库操作

```bash
# 连接到 MySQL
docker-compose exec mysql mysql -u railway -pqwe123 train

# 导出数据库
docker-compose exec mysql mysqldump -u railway -pqwe123 train > backup.sql

# 导入数据库
docker-compose exec -T mysql mysql -u railway -pqwe123 train < backup.sql

# 查看数据库日志
docker-compose logs mysql | grep ERROR
```

---

## 🔧 故障排查

### 问题 1: 容器无法启动

```bash
# 查看详细错误信息
docker-compose logs

# 检查端口是否被占用
lsof -i :8000
lsof -i :3306

# 清理并重新启动
docker-compose down
docker-compose up --build
```

### 问题 2: 数据库连接失败

```bash
# 检查 MySQL 容器状态
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 验证 MySQL 连接
docker-compose exec mysql mysqladmin ping -h localhost -u root -pqwe123

# 手动连接测试
docker-compose exec mysql mysql -u railway -pqwe123 -e "SELECT 1;"
```

### 问题 3: 应用健康检查失败

```bash
# 查看应用日志
docker-compose logs railway-py

# 手动测试健康检查
docker-compose exec railway-py curl http://localhost:8000/health

# 检查应用是否监听正确端口
docker-compose exec railway-py netstat -tlnp | grep 8000
```

### 问题 4: 数据持久化问题

```bash
# 查看数据卷
docker volume ls

# 检查数据卷详情
docker volume inspect railway-py_mysql_data

# 备份数据卷
docker run --rm -v railway-py_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz -C /data .
```

---

## 🔄 更新部署

### 代码更新

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并启动
docker-compose up --build -d railway-py

# 3. 查看日志确认启动成功
docker-compose logs -f railway-py
```

### 依赖更新

```bash
# 1. 修改 requirements.txt

# 2. 重新构建镜像（不使用缓存）
docker-compose build --no-cache railway-py

# 3. 重启服务
docker-compose up -d railway-py
```

---

## 🔒 生产环境建议

### 1. 使用环境变量文件

创建 `.env` 文件:

```env
# MySQL 配置
MYSQL_ROOT_PASSWORD=your_strong_password_here
MYSQL_DATABASE=train
MYSQL_USER=railway
MYSQL_PASSWORD=your_strong_password_here

# 应用配置
DB_HOST=mysql
DB_PORT=3306
DB_USER=railway
DB_PASSWORD=your_strong_password_here
DB_NAME=train
DB_CHARSET=utf8mb4
```

修改 `docker-compose.yml` 使用 `env_file`:

```yaml
services:
  mysql:
    env_file:
      - .env
    # ...
  
  railway-py:
    env_file:
      - .env
    # ...
```

**⚠️ 重要**: 将 `.env` 添加到 `.gitignore`

### 2. 限制资源使用

```yaml
services:
  railway-py:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. 配置日志轮转

```yaml
services:
  railway-py:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. 使用 Nginx 反向代理

参考项目中的 `nginx/railway-py.conf` 配置

### 5. 启用 SSL/TLS

在生产环境中使用 HTTPS，配置 Nginx 证书

---

## 📊 监控和维护

### 查看容器资源使用

```bash
# 实时监控
docker stats

# 查看磁盘使用
docker system df

# 清理未使用资源
docker system prune -a
```

### 定期备份

```bash
# 创建备份脚本 backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T mysql mysqldump -u railway -pqwe123 train > backup_${DATE}.sql
```

---

## 📚 附录

### 端口说明

| 服务 | 容器端口 | 宿主机端口 | 说明 |
|------|----------|------------|------|
| MySQL | 3306 | 3306 | 数据库服务 |
| Railway-py | 8000 | 8000 | FastAPI 应用 |

### 数据卷说明

| 卷名 | 挂载点 | 用途 |
|------|--------|------|
| mysql_data | /var/lib/mysql | MySQL 数据持久化 |
| ./logs | /app/logs | 应用日志 |
| ./init.sql | /docker-entrypoint-initdb.d/init.sql | 数据库初始化脚本 |

### 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 3306 | 数据库端口 |
| DB_USER | root | 数据库用户 |
| DB_PASSWORD | qwe123 | 数据库密码 |
| DB_NAME | train | 数据库名称 |
| DB_CHARSET | utf8mb4 | 字符集 |

---

## 🆘 获取帮助

- 查看 FastAPI 文档: http://localhost:8000/docs
- 查看项目 README: `README.md`
- Docker Compose 官方文档: https://docs.docker.com/compose/

---

**文档版本**: 1.0  
**最后更新**: 2025-12-02
