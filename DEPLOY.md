# GitHub自动部署到阿里云服务器配置指南

## 📋 前置条件

1. ✅ 阿里云服务器已安装Docker
2. ✅ SSH可以正常访问服务器
3. ✅ 代码已推送到GitHub

## 🔐 配置GitHub Secrets

在GitHub仓库页面，进入 `Settings` > `Secrets and variables` > `Actions`，点击 `New repository secret` 添加以下密钥：

### 必需的Secrets：

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `ALIYUN_HOST` | 阿里云服务器IP地址 | `123.456.789.123` |
| `ALIYUN_USER` | 服务器登录用户名 | `root` 或 `ubuntu` |
| `ALIYUN_SSH_KEY` | SSH私钥内容 | 私钥文件完整内容 |
| `ALIYUN_PORT` | SSH端口 | `22` (默认) |

### 获取SSH私钥的方法：

1. **方法一：使用现有密钥**
   ```bash
   cat ~/.ssh/id_rsa
   ```

2. **方法二：生成新密钥（推荐）**
   ```bash
   # 生成新的SSH密钥对
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/railway_deploy_key -C "deploy@railway-py"
   
   # 查看私钥（复制到GitHub Secrets）
   cat ~/.ssh/railway_deploy_key
   
   # 查看公钥（添加到服务器）
   cat ~/.ssh/railway_deploy_key.pub
   ```

3. **将公钥添加到服务器**
   ```bash
   # 在服务器上执行
   mkdir -p ~/.ssh
   echo "公钥内容" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

## 🚀 自动部署流程

配置完成后，每次推送代码到 `master` 分支时，会自动触发以下流程：

1. **代码更新** - 在服务器上拉取最新代码
2. **停止旧容器** - 停止并删除现有的Docker容器
3. **构建新镜像** - 使用最新代码构建Docker镜像
4. **启动新容器** - 运行新的Docker容器
5. **健康检查** - 测试服务是否正常启动
6. **清理资源** - 清理不需要的Docker镜像

## 🔧 手动部署选项

如果需要手动部署，可以使用提供的脚本：

```bash
# 在服务器上执行
wget https://raw.githubusercontent.com/maius28/railway-py/master/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## 📊 监控和管理

### 查看部署日志
在GitHub Actions页面查看部署日志：
`GitHub仓库` > `Actions` > 点击最新的workflow运行

### 服务器端管理命令

```bash
# 查看容器状态
docker ps | grep railway-py

# 查看应用日志
docker logs railway-py -f

# 重启应用
docker restart railway-py

# 停止应用
docker stop railway-py

# 删除应用
docker stop railway-py && docker rm railway-py
```

### 测试服务

```bash
# 本地测试
curl http://localhost:8000/ping

# 远程测试
curl http://服务器IP:8000/ping
```

## 🛠️ 故障排除

### 常见问题

1. **SSH连接失败**
   - 检查服务器IP和端口
   - 确认SSH密钥格式正确
   - 检查服务器防火墙设置

2. **Docker构建失败**
   - 检查Dockerfile语法
   - 确认requirements.txt文件存在
   - 查看构建日志

3. **容器启动失败**
   - 检查端口是否被占用
   - 查看容器日志：`docker logs railway-py`
   - 确认应用代码无错误

4. **服务无法访问**
   - 检查防火墙设置：`sudo ufw allow 8000`
   - 检查阿里云安全组规则
   - 确认容器端口映射正确

### 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 📞 支持

如果遇到问题，请检查：
1. GitHub Actions日志
2. 服务器上的Docker日志
3. 网络连接和防火墙设置

---

配置完成后，每次 `git push` 都会自动部署到服务器！🎉
