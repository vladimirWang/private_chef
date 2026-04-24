FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依赖优先拷贝，提升构建缓存命中
COPY pyproject.toml uv.lock /app/

# 严格按 uv.lock 安装（不允许解析变化）
RUN uv sync --frozen --no-dev

COPY app /app/app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
