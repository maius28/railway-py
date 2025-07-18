# railway-py

本项目基于 FastAPI，旨在封装 Python 算法并通过 HTTP 接口对外提供服务，便于其他服务调用。

## 目录结构

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