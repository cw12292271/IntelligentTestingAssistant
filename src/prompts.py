"""Prompt 模板 """
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

TEST_EXPERT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一名资深测试工程师，擅长分析需求、设计测试用例。"
               "请关注边界条件、异常场景和数据组合。"),
    MessagesPlaceholder(variable_name="history"),   # 历史消息占位符
    ("human", "{input}"),                            # 当前用户输入
])