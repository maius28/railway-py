# Railway-PY

本项目基于 FastAPI，旨在封装 Python 算法并通过 HTTP 接口对外提供服务，便于其他服务调用。

## 🚀 自动部署

本项目支持通过 GitHub Actions 自动部署到阿里云服务器。每次推送到 master 分支时，将自动触发构建和部署流程。

## 📋 部署前准备

### 1. 配置 GitHub Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下密钥：

- `ALIYUN_HOST`: 阿里云服务器IP地址
- `ALIYUN_USER`: 服务器用户名（通常是 root）
- `ALIYUN_SSH_KEY`: SSH私钥内容
- `ALIYUN_PORT`: SSH端口（通常是 22）

### 2. 服务器环境准备

在阿里云服务器上执行以下命令：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建应用目录
sudo mkdir -p /opt/railway-py
sudo chown $USER:$USER /opt/railway-py

# 重启以应用Docker组权限
sudo reboot
```

### 3. 配置 Nginx（可选）

```bash
# 安装 Nginx
sudo apt install nginx -y

# 复制配置文件
sudo cp nginx/railway-py.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/railway-py.conf /etc/nginx/sites-enabled/

# 测试配置并重启
sudo nginx -t
sudo systemctl reload nginx
```

```
railway-py/
├── app/
│   ├── api/
│   │   └── v1/ #接口代码
│   │       └── endpoints.py
│   ├── core/
│   │   ├── config.py
│   │   └── error_handler.py
│   ├── models/ #参数和返回对象
│   │   └── response.py 
│   ├── services/
│   │   └── algorithm.py #算法代码
│   └── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动服务：
   ```bash
   uvicorn app.main:app --reload
   ```
3. 通过 Docker 启动：
   ```bash
   docker build -t railway-py .
   docker run -p 8000:8000 railway-py
   ```

## 算法代码集成
1. 拷贝算法代码到/services目录中
2. 在models/文件夹下创建自己的http响应参数的返回值
3. app/api/vi/endpoints.py文件中创建http方法，接收http参数->参数转换成算法入口参数->调用算法方法->方法返回值转换成http返回对象

## 主要功能
- 封装 Python 算法为 HTTP 接口
- 统一 JSON 返回结构
- 标准化错误处理 