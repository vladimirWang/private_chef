from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.schemas import ChatRequest
from app.services.chat_service import (
    append_assistant_message,
    append_user_message,
    clear_messages,
    get_messages,
    mock_markdown_answer,
    text_stream,
)

router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话（mock）"""
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    await append_user_message(request.thread_id, request.message, request.image_url)

    answer = mock_markdown_answer(request.message, request.image_url)

    async def streamer():
        collected: list[str] = []
        async for chunk in text_stream(answer):
            collected.append(chunk)
            yield chunk

        await append_assistant_message(request.thread_id, "".join(collected))

    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8")


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息（mock）"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    messages = await get_messages(thread_id)

    return JSONResponse(content={"messages": messages})


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息（mock）"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    await clear_messages(thread_id)

    return JSONResponse(content={"ok": True})