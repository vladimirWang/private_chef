FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依赖优先拷贝，提升构建缓存命中
COPY pyproject.toml uv.lock /app/

# 安装 uv，并同步依赖（使用 uv.lock 锁定）
RUN pip install --no-cache-dir uv && \
    uv sync --frozen

COPY app /app/app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--env-file", ".env.prod"]
