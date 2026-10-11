"""文本切分：中文友好的 RecursiveCharacterTextSplitter。"""
from langchain_text_splitters import RecursiveCharacterTextSplitter,CharacterTextSplitter


def get_splitter(chunk_size: int = 500, chunk_overlap: int = 50):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        # separator="\n\n",              # 单个字符串，不是列表
        length_function=len,
        add_start_index=True,
    )