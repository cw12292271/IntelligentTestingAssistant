"""RAG 问答链：检索 → 拼 Prompt → 调 LLM。"""
from langchain_core.prompts import ChatPromptTemplate
from src.llm import get_llm
from src.rag.vectorstore import get_retriever
from src.rag.reranker import rerank


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是测试专家。请严格基于以下资料回答问题，资料里没有的内容不要编造。\n\n资料：\n{context}"),
    ("human", "{question}"),
])



def build_rag_chain(
        k: int = 5, 
        fetch_k: int = 50, 
        use_rerank: bool = True,
        use_hybrid: bool = False,
        ):
    """构建 RAG 链。

    Args:
        k: 最终送给 LLM 的文档数
        fetch_k: 向量检索先召回的候选数
        use_rerank: 是否启用 Rerank
        use_hybrid: 是否使用混合检索（BM25 + 向量）
    """
    if use_hybrid:
        from src.rag.hybrid_retriever import build_hybrid_retriever
        retriever = build_hybrid_retriever(k=k, fetch_k=fetch_k)
    else:
        from src.rag.vectorstore import get_retriever
        retriever = get_retriever(k=fetch_k)
    # retriever = get_retriever(k=fetch_k)
    llm = get_llm()
    def rag_answer(question: str) -> str:
        try:
            # docs = retriever(question)  
            # docs = retriever.invoke(question)   # 注意：EnsembleRetriever 用 invoke   混合检索用 retriever.invoke(question)（LangChain Retriever 标准接口）            
            # 🌟 核心修复：判断有没有 invoke 方法
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(question)   # 混合检索（LangChain 对象）
            else:
                docs = retriever(question)          # 自封装检索（普通函数）
            if use_rerank:
                docs = rerank(question, docs, top_k=k)
            context = "\n\n".join(d.page_content for d in docs)
            prompt = RAG_PROMPT.format_messages(context=context, question=question)
            # 改成流式
            for chunk in llm.stream(prompt):
                print(chunk.content, end="", flush=True)
            print()
            # return llm.invoke(prompt).content
            # 引用溯源
            if docs:
                print("\n📚 参考资料：")
                seen = set()
                for d in docs:
                    meta = d.metadata or {}
                    source = meta.get("source", "未知")
                    # 只取文件名
                    import os
                    source_name = os.path.basename(str(source))
                    sheet = meta.get("sheet", "")
                    row = meta.get("row", "")
                    
                    # 拼一个唯一 key 去重
                    key = f"{source_name}|{sheet}|{row}"
                    if key in seen:
                        continue
                    seen.add(key)

                    # 拼展示格式
                    parts = [f"`{source_name}`"]
                    if sheet:
                        parts.append(f"Sheet: {sheet}")
                    if row != "":
                        parts.append(f"第 {int(row) + 2} 行")  # +2 因为 pandas 行号从 0 开始，Excel 从表头后第 1 行算
                    
                    print(f"  {len(seen)}. {' | '.join(parts)}")
        except Exception as e:
            print(f"调用失败：{e}")

    return rag_answer

