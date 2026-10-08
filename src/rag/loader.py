"""文档加载：支持 docx / txt / pdf。"""
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader, CSVLoader, Docx2txtLoader, TextLoader, PyPDFLoader


def load_documents(file_path: str) -> List[Document]:
    """根据文件后缀选择加载器。"""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    elif suffix == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".csv":
        loader = CSVLoader(str(path))
    else:
        raise ValueError(f"不支持的文件类型：{suffix}")

    return loader.load()