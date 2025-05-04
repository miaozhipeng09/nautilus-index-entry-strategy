# tools/process_csv_to_parquet.py

import os
from pathlib import Path
import pandas as pd

def process_csv_to_parquet():
    csv_folder = Path(r"C:\Users\M\PythonProject6\Trade\stock_data")
    output_folder = Path(r"C:\Users\M\PythonProject6\Trade\parquet_catalog")

    output_folder.mkdir(parents=True, exist_ok=True)

    all_records = []
    instrument_records = []

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
                        "instrument_id": f"{ticker}.SIM",
                        "open_time": dt,
                        "open": float(df.loc[dt, open_col]),
                        "high": float(df.loc[dt, high_col]),
                        "low": float(df.loc[dt, low_col]),
                        "close": float(df.loc[dt, close_col]),
                        "volume": float(df.loc[dt, volume_col]),
                        "bar_type": "TIME_1D",
                        "price_type": "MID",
                        "venue": "SIM",
                    }
                    all_records.append(record)

                # 补充每个股票的 instrument
                instrument_record = {
                    "instrument_id": f"{ticker}.SIM",
                    "type": "STOCK",
                    "symbol": ticker,
                    "base_currency": "USD",
                    "quote_currency": "USD",
                    "tick_size": 0.01,
                    "lot_size": 1.0,
                    "min_size": 1.0,
                    "max_size": 1000000.0,
                    "margin": 1.0,
                }
                instrument_records.append(instrument_record)

            except Exception as e:
                print(f"⚠️ Failed to load {filename}: {e}")
                continue

    print(f"✅ Successfully loaded {len(all_records)} bars.")

    # 保存bars
    df_all = pd.DataFrame(all_records)
    for instrument_id in df_all["instrument_id"].unique():
        df_symbol = df_all[df_all["instrument_id"] == instrument_id]
        symbol_path = output_folder / f"{instrument_id.split('.')[0]}.parquet"
        df_symbol.to_parquet(symbol_path, index=False)
        print(f"✅ Saved {instrument_id} bars to {symbol_path}")

    # 保存_instruments.parquet
    df_instruments = pd.DataFrame(instrument_records)
    instrument_path = output_folder / "_instruments.parquet"
    df_instruments.to_parquet(instrument_path, index=False)
    print(f"🎯 Saved instruments metadata to {instrument_path}")

    print(f"🎯 All symbols and instruments saved successfully into {output_folder}")

if __name__ == "__main__":
    process_csv_to_parquet()
