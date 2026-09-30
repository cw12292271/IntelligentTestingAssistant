"""Pydantic 模型定义，用于结构化输出。"""
from pydantic import BaseModel, Field
from typing import List

class TestCase(BaseModel):
    """单条测试用例"""
    title: str = Field(description="用例标题")
    precondition: str = Field(description="前置条件")
    steps: List[str] = Field(description="操作步骤列表")
    expected: str = Field(description="预期结果")
    case_type: str = Field(description="用例类型：正常/边界/异常")

# ---- API 请求/响应模型 ----
class ChatRequest(BaseModel):
    session_id: str = Field(description="会话ID，用于隔离不同用户")
    message: str = Field(min_length=1, description="用户消息")

class ChatResponse(BaseModel):
    reply: str = Field(description="助手回复")