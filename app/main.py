from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.v1 import chat
from app.api.v1 import oss
from app.common.logger import setup_logging
import os
load_dotenv()
appenv = os.getenv("APP_ENV")

# 初始化日志配置
setup_logging()

app = FastAPI(
    title="Private Chef API",
    description="AI 私人厨师",
    version="0.1.0"
)

# 临时放开：允许任意来源跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # 允许任意来源时不能开启 credentials（浏览器会拒绝 Access-Control-Allow-Origin: * + credentials）
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(oss.router, prefix="/api/v1", tags=["申请上传签名url"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

if __name__=="__main__":
    import uvicorn
    # 启动命令: python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)