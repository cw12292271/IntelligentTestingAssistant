"""查看 Excel 文件的 sheet 和列结构。"""
import pandas as pd
from pathlib import Path

for file in ["02_bug记录.xlsx", "05_测试用例文档.xlsx"]:
    path = Path("asset/rag_docs") / file
    if not path.exists():
        print(f"❌ 找不到 {path}")
        continue

    print(f"\n{'='*60}")
    print(f"文件: {file}")
    print(f"{'='*60}")

    xls = pd.ExcelFile(path)
    print(f"sheet 列表: {xls.sheet_names}")

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        print(f"\n--- sheet: {sheet_name} ---")
        print(f"行数: {len(df)}, 列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        if not df.empty:
            print(f"第一行样例:")
            for col, val in df.iloc[0].items():
                val_str = str(val)[:80] + "..." if len(str(val)) > 80 else str(val)
                print(f"  {col}: {val_str}")