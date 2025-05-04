import pandas as pd
import yfinance as yf
import os
from datetime import timedelta

# 文件路径
excel_path = "./Index Add Event Data.xlsx"

# 读取第二个Sheet（注意：sheet_name=1，索引从0开始）
events_sheet = pd.read_excel(excel_path, sheet_name=1)

# 打印一下列名，确认
print("实际列名：", events_sheet.columns.tolist())

# 标准化列名（去掉空格）
events_sheet.columns = events_sheet.columns.str.strip()

# 转换日期格式
events_sheet["Announced"] = pd.to_datetime(events_sheet["Announced"])
events_sheet["Trade Date"] = pd.to_datetime(events_sheet["Trade Date"])

# 创建保存数据的文件夹
output_dir = "../stock_data"
os.makedirs(output_dir, exist_ok=True)

# 拉取时间区间
pre_days = 20
post_days = 5

# 开始循环每一条事件
for idx, row in events_sheet.iterrows():
    ticker = row["Ticker"]
    announced = row["Announced"]
    trade_date = row["Trade Date"]

    # 简单清理Ticker（去掉US，留主要部分）
    ticker_clean = ticker.split(" ")[0]

    start_date = announced - timedelta(days=pre_days)
    end_date = trade_date + timedelta(days=post_days)

    print(f"拉取 {ticker_clean}: {start_date.date()} 到 {end_date.date()}")

    try:
        # 拉取行情数据
        df = yf.download(
            ticker_clean,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
        )

        if not df.empty:
            df.to_csv(f"{output_dir}/{ticker_clean}_{announced.date()}.csv")
        else:
            print(f"⚠️ {ticker_clean} 没有数据。")

    except Exception as e:
        print(f"❌ 拉取 {ticker_clean} 失败，错误信息：{e}")

print("\n🎯 全部行情拉取完成！")
