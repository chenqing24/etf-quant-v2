#!/usr/bin/env python3
"""
PoC: Backtesting.py 与 v2 数据兼容性验证

目标：跑通 1 只 ETF + 1 个简单策略，验证三件事
1. SQLite 数据可被 Backtesting.py 读取
2. v2 27 因子接口可与 Backtesting.py Strategy 对接
3. 输出 Sharpe/MaxDD/Return 与 v1 时代结果量级一致
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
sys.path.insert(0, str(SRC_ROOT))

import sqlite3
import pandas as pd
from backtesting import Backtest, Strategy


def load_etf_data(code: str) -> pd.DataFrame:
    """从 SQLite 读 ETF 日线，转 Backtesting.py 格式"""
    db_path = PROJECT_ROOT / 'data' / 'etf.db'
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM daily WHERE code=? ORDER BY date",
        conn, params=(code,)
    )
    conn.close()

    # Backtesting.py 要求列名大写 + DatetimeIndex
    df = df.rename(columns={
        'date': 'Date', 'open': 'Open', 'high': 'High',
        'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    return df


class SmaCross(Strategy):
    """简单均线交叉策略（PoC 用，不上 27 因子）"""
    n_fast = 5
    n_slow = 20

    def init(self):
        close = pd.Series(self.data.Close)
        self.sma_fast = self.I(lambda: close.rolling(self.n_fast).mean())
        self.sma_slow = self.I(lambda: close.rolling(self.n_slow).mean())

    def next(self):
        if self.sma_fast[-2] < self.sma_slow[-2] and self.sma_fast[-1] > self.sma_slow[-1]:
            self.buy()
        elif self.sma_fast[-2] > self.sma_slow[-2] and self.sma_fast[-1] < self.sma_slow[-1]:
            self.position.close()


def main():
    code = '512170'  # 医疗ETF华宝
    print(f"📊 PoC: {code} + SMA Cross 策略 + Backtesting.py")
    print("=" * 60)

    df = load_etf_data(code)
    print(f"数据范围: {df.index[0].date()} ~ {df.index[-1].date()} ({len(df)} 条)")
    print(f"列: {list(df.columns)}")
    print(f"Close 范围: {df['Close'].min():.3f} ~ {df['Close'].max():.3f}")

    bt = Backtest(df, SmaCross, cash=100000, commission=0.001)
    stats = bt.run()

    print("\n" + "=" * 60)
    print("📈 回测结果（Backtesting.py）:")
    print(f"  总收益:    {stats['Return [%]']:.2f}%")
    print(f"  年化收益:  {stats['Return (Ann.) [%]']:.2f}%")
    print(f"  Sharpe:    {stats['Sharpe Ratio']:.2f}")
    print(f"  最大回撤:  {stats['Max. Drawdown [%]']:.2f}%")
    print(f"  交易次数:  {stats['# Trades']}")
    print(f"  胜率:      {stats['Win Rate [%]']:.2f}%")
    print("=" * 60)

    # 验证：量级是否合理
    assert len(df) > 100, "数据太少"
    assert stats['# Trades'] > 0, "策略没触发交易"
    assert -50 < stats['Max. Drawdown [%]'] < 0, "最大回撤异常"

    print("\n✅ PoC 通过：Backtesting.py 与 v2 SQLite 数据兼容")


if __name__ == '__main__':
    main()