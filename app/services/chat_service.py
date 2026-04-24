import asyncio
from typing import Dict, List, Literal, Optional, TypedDict

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


def build_user_content(message: str, image_url: Optional[str]) -> str | List[ContentPart]:
    if not image_url:
        return message

    parts: List[ContentPart] = []
    if message.strip():
        parts.append({"type": "text", "text": message})
    parts.append({"type": "image", "url": image_url})
    return parts


def mock_markdown_answer(message: str, image_url: Optional[str]) -> str:
    user_text = message.strip() if message.strip() else "（未输入文字，仅上传图片）"
    has_image = "有（已上传）" if image_url else "无"

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


async def text_stream(text: str, *, chunk_size: int = 32, delay_s: float = 0.01):
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
        await asyncio.sleep(delay_s)


async def append_user_message(thread_id: str, message: str, image_url: Optional[str]):
    user_content = build_user_content(message, image_url)
    async with _LOCK:
        _THREAD_MESSAGES.setdefault(thread_id, []).append({"role": "user", "content": user_content})


async def append_assistant_message(thread_id: str, content: str):
    async with _LOCK:
        _THREAD_MESSAGES.setdefault(thread_id, []).append({"role": "assistant", "content": content})


async def get_messages(thread_id: str) -> List[StoredMessage]:
    async with _LOCK:
        return list(_THREAD_MESSAGES.get(thread_id, []))


async def clear_messages(thread_id: str):
    async with _LOCK:
        _THREAD_MESSAGES[thread_id] = []

