"""文档加载：支持 docx / txt / pdf/csv/md。"""
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader, CSVLoader, Docx2txtLoader, TextLoader, PyPDFLoader,UnstructuredExcelLoader


def load_documents(file_path: str) -> List[Document]:
    """根据文件后缀选择加载器。"""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    # elif suffix == ".xlsx":
    #     loader = UnstructuredExcelLoader(str(path), mode="elements")
    elif suffix in [".xlsx", ".xls"]:
        # loader = UnstructuredExcelLoader(str(path))
        return _load_excel(path)
    elif suffix == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".csv":
        loader = CSVLoader(str(path))
    elif suffix == ".md":
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件类型：{suffix}")

    return loader.load()


def _load_excel(path: Path) -> List[Document]:
    """读 Excel 的 RAG文本 列，每行一个 Document。"""
    import pandas as pd

    docs = []
    xls = pd.ExcelFile(path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        if df.empty:
            continue

        if "RAG文本" in df.columns:
            # 优先用 RAG文本 列
            for idx, row in df.iterrows():
                content = str(row["RAG文本"]).strip()
                if content and content != "nan":
                    docs.append(Document(
                        page_content=content,
                        metadata={
                            "source": str(path),
                            "sheet": sheet_name,
                            "row": idx,
                            "no_split": True,   # ← 标记不切分
                        },
                    ))
        else:
            # 降级：整行拼
            for idx, row in df.iterrows():
                content = f"[{sheet_name}] " + " | ".join(
                    f"{col}: {val}" for col, val in row.items() if pd.notna(val)
                )
                docs.append(Document(
                    page_content=content,
                    metadata={
                        "source": str(path),
                        "sheet": sheet_name,
                        "row": idx,
                        "no_split": True,   # ← 标记不切分
                    },
                ))
    return docs