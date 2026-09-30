import os

from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from src.config import *  # 触发 .env 加载

# def get_llm(temperature: float = 0.7) -> ChatOpenAI:
#     return ChatOpenAI(
#         model=os.getenv("ARK_MODEL"),
#         base_url=os.getenv("ARK_BASE_URL"),
#         api_key=os.getenv("ARK_API_KEY"),
#         temperature=temperature,
#     )

def get_llm(temperature: float = 0.7):
    model = init_chat_model(
        model=os.getenv("ARK_MODEL"),
        model_provider="openai",
        api_key=os.getenv("ARK_API_KEY"),
        base_url=os.getenv("ARK_BASE_URL"),
        temperature=temperature,
    )
    return model
