# Nautilus Index Entry Strategy

This project implements an **event-driven trading strategy** using [NautilusTrader](https://github.com/nautechsystems/nautilus-trader), focused on **index constituent changes** — specifically, how stocks respond when they are added to an index.

## 📌 Strategy Overview

When a stock is **announced to join a major index**, institutional investors and ETFs are typically forced to buy it by the effective date. This strategy aims to exploit **price drift** between the **announcement date** and the **final entry date**.

Key characteristics:

- 📈 **Event-driven logic**: Signals are triggered by index inclusion announcements.
- 🕗 **Timed entries**: Long or short positions are entered one day after the announcement.
- 📊 **Fixed holding period**: Positions are held until 2 days after the index entry date.
- ⚙️ **Backtested** using high-resolution data with `NautilusTrader`.

## 🧠 Features

- Configurable `price_change_threshold` to filter significant events
- Supports loading index event data from custom files (e.g., `.xlsx`)
- Handles position sizing, execution logic, and timed exits
- Built-in integration with the NautilusTrader simulation engine

## 📂 Project Structure

/Trade
├── strategy/
│ └── dynamic_event_strategy.py # Core strategy class
├── models/
│ └── event_loader.py # Loads index entry event data
├── config/
│ └── dynamic_event_strategy_config.py # Strategy config class
├── run_backtest.py # Entry point for backtesting

markdown
复制
编辑

## 🔧 Dependencies

- `nautilus-trader`
- `pandas`
- `openpyxl` (if you're loading `.xlsx` files)

Install dependencies (inside your virtual environment):

```bash
pip install -r requirements.txt
🚀 Quick Start
bash
复制
编辑
# Set up the virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run backtest
python run_backtest.py
📈 Example Use Case
Use this strategy to study:

Abnormal returns before ETF inclusion

Market impact of passive fund flows

Event-based alpha generation with minimal lookahead bias

🧪 Status
This is a research-stage project, created for experimentation and learning purposes. It can be expanded with:

Dynamic thresholding using reinforcement learning (e.g., PPO)

Integration of order book signals

Risk-adjusted portfolio allocation

📜 License
MIT License.

