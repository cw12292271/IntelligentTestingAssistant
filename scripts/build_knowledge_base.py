"""把 asset/rag_docs/ 下的文档全部加载、切分、入库。"""
from pathlib import Path
from src.rag.loader import load_documents
from src.rag.splitter import get_splitter
from src.rag.vectorstore import add_documents

splitter = get_splitter()
all_docs = []
for f in Path("asset/rag_docs").glob("*"):
    if f.suffix.lower() in [".docx", ".xlsx", ".xls", ".txt", ".pdf", ".csv", ".md"]:
        try:
            docs = load_documents(str(f))
            # Excel 来的不切分
            if docs and docs[0].metadata.get("no_split"):
                all_docs.extend(docs)
                print(f"{f.name}: {len(docs)} chunks（不切分）")
            else:
                chunks = splitter.split_documents(docs)
                all_docs.extend(chunks)
                print(f"{f.name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"{f.name}: 加载失败（{e}）")
    else:
        print(f"{f.name}: 不支持的类型，跳过")

add_documents(all_docs)
print(f"共入库 {len(all_docs)} 个 chunk")
