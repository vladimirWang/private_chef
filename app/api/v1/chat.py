import asyncio
from typing import Dict, List, Literal, Optional, TypedDict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.schemas import ChatRequest

router = APIRouter()

# ---- 前端期望的最小数据格式 ----
# 1) /chat/stream：返回纯文本流（前端直接拼接展示，支持 Markdown）
# 2) /chat/messages：返回 { messages: [{role, content}, ...] }
#    - content 为 string 或多模态数组 [{type:"text", text}, {type:"image", url}]

Role = Literal["user", "assistant"]


class ContentPart(TypedDict, total=False):
    type: Literal["text", "image"]
    text: str
    url: str


class StoredMessage(TypedDict):
    role: Role
    content: str | List[ContentPart]


_THREAD_MESSAGES: Dict[str, List[StoredMessage]] = {}
_LOCK = asyncio.Lock()


def _build_user_content(message: str, image_url: Optional[str]) -> str | List[ContentPart]:
    if not image_url:
        return message

    parts: List[ContentPart] = []
    if message.strip():
        parts.append({"type": "text", "text": message})
    parts.append({"type": "image", "url": image_url})
    return parts


def _mock_markdown_answer(message: str, image_url: Optional[str]) -> str:
    user_text = message.strip() if message.strip() else "（未输入文字，仅上传图片）"
    has_image = "有（已上传）" if image_url else "无"

    # 尽量用前端 `ReactMarkdown + remark-gfm` 能漂亮展示的结构（标题/列表/代码块/表格）
    return (
        "## ✅ 收到，我来当你的 AI 私人厨师\n\n"
        "### 你提供的内容\n"
        f"- **文字**：{user_text}\n"
        f"- **图片**：{has_image}\n\n"
        "### 我会怎么做（mock 展示）\n"
        "1. 识别食材（如果有图片）并补全可能的调料\n"
        "2. 给出 2-3 道适配度高的菜\n"
        "3. 每道菜包含：难度 / 用时 / 调料 / 步骤\n\n"
        "---\n\n"
        "## 🍳 推荐食谱（示例）\n\n"
        "### 1) 番茄炒蛋\n"
        "- **适配度**：4.5/5（经典快手菜，成功率高）\n"
        "- **难度**：简单\n"
        "- **用时**：10 分钟\n"
        "- **所需调料**：盐、糖（少许提鲜）、生抽（可选）\n"
        "- **步骤**：\n"
        "  1. 鸡蛋加少许盐打散，热锅滑炒至凝固盛出\n"
        "  2. 番茄切块下锅，炒出汁后加少许盐/糖\n"
        "  3. 回锅鸡蛋，翻匀即可\n\n"
        "### 2) 蒜香青菜\n"
        "- **适配度**：4.0/5（下饭、最快）\n"
        "- **难度**：简单\n"
        "- **用时**：5 分钟\n"
        "- **所需调料**：蒜末、盐、少许油\n"
        "- **步骤**：\n"
        "  1. 热锅冷油，下蒜末爆香\n"
        "  2. 大火快炒青菜 30-60 秒，加盐出锅\n\n"
        "### 3) 酱油炒饭（如果有隔夜饭）\n"
        "- **适配度**：3.5/5（看你是否有米饭）\n"
        "- **难度**：简单\n"
        "- **用时**：12 分钟\n"
        "- **所需调料**：生抽、老抽（可选）、葱花\n"
        "- **步骤**：\n"
        "  1. 鸡蛋先炒散\n"
        "  2. 下米饭炒散后沿锅边淋生抽\n"
        "  3. 翻炒均匀，撒葱花\n\n"
        "---\n\n"
        "## 🧾 一张清单（示例表格）\n\n"
        "| 菜名 | 难度 | 用时 | 适配度 |\n"
        "|---|---:|---:|---:|\n"
        "| 番茄炒蛋 | 简单 | 10min | 4.5 |\n"
        "| 蒜香青菜 | 简单 | 5min | 4.0 |\n"
        "| 酱油炒饭 | 简单 | 12min | 3.5 |\n\n"
        "如果你告诉我：**有无肉类 / 主食 / 忌口**，我可以把推荐变成更贴合你家食材的版本。\n"
    )


async def _text_stream(text: str, *, chunk_size: int = 32, delay_s: float = 0.01):
    # 用小块输出，前端能看到逐字增长效果
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
        await asyncio.sleep(delay_s)


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话（mock）"""
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    user_content = _build_user_content(request.message, request.image_url)
    async with _LOCK:
        _THREAD_MESSAGES.setdefault(request.thread_id, []).append(
            {"role": "user", "content": user_content}
        )

    answer = _mock_markdown_answer(request.message, request.image_url)

    async def streamer():
        collected: List[str] = []
        async for chunk in _text_stream(answer):
            collected.append(chunk)
            yield chunk

        async with _LOCK:
            _THREAD_MESSAGES.setdefault(request.thread_id, []).append(
                {"role": "assistant", "content": "".join(collected)}
            )

    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8")


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息（mock）"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    async with _LOCK:
        messages = _THREAD_MESSAGES.get(thread_id, [])

    return JSONResponse(content={"messages": messages})


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息（mock）"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    async with _LOCK:
        _THREAD_MESSAGES[thread_id] = []

    return JSONResponse(content={"ok": True})