"""RAG 问答链：检索 → 拼 Prompt → 调 LLM。"""
from langchain_core.prompts import ChatPromptTemplate
from src.llm import get_llm
from src.rag.vectorstore import get_retriever

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是测试专家。请严格基于以下资料回答问题，资料里没有的内容不要编造。\n\n资料：\n{context}"),
    ("human", "{question}"),
])


def build_rag_chain(k: int = 5):
    retriever = get_retriever(k)
    llm = get_llm()

    def rag_answer(question: str) -> str:
        docs = retriever(question)
        context = "\n\n".join(d.page_content for d in docs)
        prompt = RAG_PROMPT.format_messages(context=context, question=question)
        return llm.invoke(prompt).content

    return rag_answer