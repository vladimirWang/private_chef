from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from app.common.logger import logger

load_dotenv()


model = init_chat_model(
    model="qwen3.5-plus",
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)

# 初始化checkpointer
connection = sqlite3.connect("resources/private_chef.db", check_same_thread=False)
checkpointer= SqliteSaver(connection)
checkpointer.setup()


tavily=TavilySearch(
    max_results=5,
    topic="general"
)
@tool
def web_search(query: str):
    """根据关键词搜索互联网"""
    return tavily.invoke(query)

system_prompt="""
你是一名私人厨师。收到用户提供的食材照片或清单后，请按以下流程操作：
1.识别和评估食材：若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份 “当前可用食材清单”。
2.智能食谱检索：优先调用 web_search 工具，以 “可用食材清单” 为核心关键词，查找可行菜谱。
3.多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名靠前。
4.结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户快速做出决策。

请严格按照流程，优先调用 web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""
agent = create_agent(
    model=model,
    tools=[web_search],
    system_prompt=system_prompt,
    checkpointer=checkpointer
)

async def search_recipes(prompt: str, image: str, thread_id: str):
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")
    try:
        # 判断是否有图片
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message=HumanMessage(content=[
                {"type": "image", "url": image},
                {"type": "text", "text": prompt}
            ])
        # 流式调用agent
        for chunk, metadata in agent.stream(
            {"message": [message]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error(f"\n[错误]: {str(e)}")
        yield "信息检索失败, 试试着手动输入食物列表"


def clear_message(thread_id: str):
    logger.info(f"清空历史消息, thread_id: {thread_id}")
    checkpointer.delete_thread(thread_id)

def get_message(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    """根据thread_id查询checkpoint"""
    cp = checkpointer.get({"configurable": {"thread_id": thread_id}})
    if not cp:
        return []
    """安全获取messages"""
    channel_values = cp.get("channel_values")
    if not channel_values:
        return []
    messages = channel_values.get("messages", [])
    if not messages:
        return []
    
    # 转换消息格式
    result = []
    for msg in messages:
        if not msg.content:
            continue
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
    return result;
