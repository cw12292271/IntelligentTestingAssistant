"""把 txt 转成 docx。"""
from docx import Document
from pathlib import Path

def txt_to_docx(txt_path: str, docx_path: str):
    doc = Document()
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            doc.add_paragraph(line.rstrip())
    doc.save(docx_path)
    print(f"已转换：{txt_path} -> {docx_path}")

if __name__ == "__main__":
    txt_to_docx("asset/rag_docs/01_测试规范.txt", "asset/rag_docs/01_测试规范.docx")
    txt_to_docx("asset/rag_docs/04_需求文档.txt", "asset/rag_docs/04_需求文档.docx")