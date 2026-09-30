"""对话链：带 Memory 的链 + 结构化输出"""
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory as ChatMessageHistory
from src.llm import get_llm
from src.prompts import TEST_EXPERT_PROMPT
from src.models import TestCase

# 1. 模型
llm = get_llm()

# 2. 链 = 提示模板 | 模型
chain = TEST_EXPERT_PROMPT | llm

# 3. 会话历史存储（按 session_id 隔离）
store = {}
def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 4. 包装成带记忆的对话链
conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 5. 结构化输出链
# 注意：此链无记忆，适合“一次性生成用例”场景
structured_llm = llm.with_structured_output(TestCase)