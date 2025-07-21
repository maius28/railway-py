FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

# 配置pip使用国内镜像源并设置重试
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --upgrade pip && \
    pip install --no-cache-dir \
                --timeout 300 \
                --retries 10 \
                --disable-pip-version-check \
                -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]