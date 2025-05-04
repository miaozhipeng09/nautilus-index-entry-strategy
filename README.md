# Nautilus Index Entry Strategy

This project implements an **event-driven trading strategy** using [NautilusTrader](https://github.com/nautechsystems/nautilus-trader), focused on **index constituent changes** — specifically, how stocks respond when they are added to an index.

# ✅ Run `run_backtest.py` to backtest an index-entry-driven equity trading strategy

This project implements a **momentum-reversion strategy** triggered by **index inclusion announcements**. It analyzes stock price reactions to constituent changes in major indices and exploits price inefficiencies using event-driven signals.

---

## 📊 Strategy Overview

When a stock is announced to be added to an index, institutional funds and ETFs often rebalance their portfolios, causing **short-term price movements**. This strategy captures such reactions using pre-defined momentum logic and executes trades accordingly.

### 📈 Signal Logic

- **Event trigger**: A stock is announced to be included in an index.
- **Entry timing**: One day after the announcement (`announce_date + 1`), we calculate the **open-to-previous-close return**.
- **Signal rule**:
  - If return **> +1%** → treated as **overreaction**, we **short** the stock (mean-reversion).
  - If return **< +1%** → interpreted as **incomplete momentum**, we **go long** (trend-following).
- **Exit logic**: All open positions are **force-closed on the day after the official index inclusion date (`trade_date + 2`)**.

---

## 🛡️ Risk Management

- Take-profit and stop-loss thresholds are applied per trade.
- Position sizing and trade frequency are adjusted to control overall portfolio volatility.
- All positions are auto-liquidated if not closed within the specified window.

---

## 📈 Backtest Results

- **Sharpe Ratio**: 1.32  
- **Sortino Ratio**: 3.67  
- **Total Return**: 14.8%  

⚠️ Note: No explicit **hedging** was applied due to data limitations. For production-level deployment, **index futures or index options** may be used to hedge portfolio exposure.

---

