import pandas as pd
from pathlib import Path

def check_instruments_parquet(parquet_path):
    df = pd.read_parquet(parquet_path)

    expected_columns = [
        "instrument_id",
        "type",
        "symbol",
        "base_currency",
        "quote_currency",
        "tick_size",
        "lot_size",
        "min_size",
        "max_size",
        "margin",
    ]

    print(f"✅ Found columns: {list(df.columns)}")

    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}")
    else:
        print("✅ All required columns exist.")

    # 检查空值
    if df.isnull().any().any():
        print("⚠️ Warning: There are missing values (NaNs) in your _instruments.parquet!")
    else:
        print("✅ No missing values.")

    # 简单展示前几行
    print("\nPreview data:")
    print(df.head())

if __name__ == "__main__":
    parquet_path = Path(r"C:\Users\M\PythonProject6\Trade\parquet_catalog\_instruments.parquet")
    check_instruments_parquet(parquet_path)
