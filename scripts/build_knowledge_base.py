"""把 asset/rag_docs/ 下的文档全部加载、切分、入库。"""
from pathlib import Path
from src.rag.loader import load_documents
from src.rag.splitter import get_splitter
from src.rag.vectorstore import add_documents


splitter = get_splitter()

all_docs = []
for f in Path("asset/rag_docs").glob("*"):
    if f.suffix.lower() in [".docx", ".txt", ".pdf", ".csv"]:
        docs = load_documents(str(f))
        chunks = splitter.split_documents(docs)
        all_docs.extend(chunks)
        print(f"{f.name}: {len(chunks)} chunks")

add_documents(all_docs)
print(f"共入库 {len(all_docs)} 个 chunk")
