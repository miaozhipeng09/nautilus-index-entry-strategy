# tools/process_csv_to_parquet.py

import os
from pathlib import Path
import pandas as pd

def process_csv_to_parquet():
    # 你的CSV文件夹位置
    csv_folder = Path(r"C:\Users\M\PythonProject6\Trade\stock_data")
    output_folder = Path(r"C:\Users\M\PythonProject6\Trade\parquet_catalog")

    # 保证输出目录存在
    output_folder.mkdir(parents=True, exist_ok=True)

    all_records = []

    files = os.listdir(csv_folder)
    print(f"📂 Found {len(files)} files in {csv_folder}.")

    for filename in files:
        if filename.lower().endswith(".csv"):
            filepath = csv_folder / filename
            print(f"🔍 Loading file: {filename}")
            try:
                df = pd.read_csv(filepath, header=[0, 1], index_col=0)
                df.index = pd.to_datetime(df.index)

                ticker = df.columns[0][1]
                print(f"✅ Detected Ticker: {ticker}")

                open_col = ('Open', ticker)
                high_col = ('High', ticker)
                low_col = ('Low', ticker)
                close_col = ('Close', ticker)
                volume_col = ('Volume', ticker)

                for dt in df.index:
                    record = {
                        "symbol": ticker,
                        "open_time": dt,
                        "open": float(df.loc[dt, open_col]),
                        "high": float(df.loc[dt, high_col]),
                        "low": float(df.loc[dt, low_col]),
                        "close": float(df.loc[dt, close_col]),
                        "volume": float(df.loc[dt, volume_col]),
                        "bar_type": "TIME_1D",
                    }
                    all_records.append(record)

            except Exception as e:
                print(f"⚠️ Failed to load {filename}: {e}")
                continue

    print(f"✅ Successfully loaded {len(all_records)} records.")

    # 将所有数据转成DataFrame
    df_all = pd.DataFrame(all_records)

    # 按symbol分别保存成Parquet
    for symbol in df_all["symbol"].unique():
        df_symbol = df_all[df_all["symbol"] == symbol]
        symbol_path = output_folder / f"{symbol}.parquet"
        df_symbol.to_parquet(symbol_path, index=False)
        print(f"✅ Saved {symbol} to {symbol_path}")

    print(f"🎯 All symbols saved successfully into {output_folder}")

if __name__ == "__main__":
    process_csv_to_parquet()
