#!/usr/bin/env python3
"""
增量更新 core 池 ETF 数据（14 只）到 SQLite

数据源：腾讯财经 ifzq.gtimg.cn（按 SOUL.md 规则 29 接入验证后记录）
- 接口：http://ifzq.gtimg.cn/appstock/app/fqkline/get
- 字段：日期, 开, 收, 高, 低, 成交量
- 限速：≥5 秒/次（aktools 限速规范）
- 写入：DataWriter（SOUL.md 规则 16：数据源统一 SQLite）
"""
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
sys.path.insert(0, str(SRC_ROOT))

import requests
import json
import sqlite3
import pandas as pd

from etf_quant.data_layer.writer import DataWriter

TENCENT_URL = 'http://ifzq.gtimg.cn/appstock/app/fqkline/get'
INTERVAL = 5.5  # 秒，aktools 限速规范


def get_core_etfs():
    conn = sqlite3.connect(PROJECT_ROOT / 'data' / 'etf.db')
    cur = conn.cursor()
    cur.execute("SELECT code FROM etf_names WHERE pool_role='core' ORDER BY code")
    codes = [r[0] for r in cur.fetchall()]
    conn.close()
    return codes


def fetch_tencent(code: str, n: int = 320) -> pd.DataFrame:
    """腾讯历史 K 线：返回 date, open, high, low, close, volume"""
    if code.startswith('5') or code.startswith('6'):
        symbol = f'sh{code}'
    elif code.startswith('1'):
        symbol = f'sz{code}'
    else:
        symbol = f'sz{code}'

    r = requests.get(
        TENCENT_URL,
        params={'param': f'{symbol},day,,,{n},qfq', '_var': 'kline_dayqfq'},
        timeout=15,
    )
    r.raise_for_status()
    payload = json.loads(r.text.lstrip('kline_dayqfq='))
    rows = payload['data'][symbol].get('qfqday') or payload['data'][symbol].get('day')
    if not rows:
        return pd.DataFrame()

    # 字段：日期, 开, 收, 高, 低, 成交量  → 重命名为标准 OHLC
    df = pd.DataFrame(rows, columns=['date', 'open', 'close', 'high', 'low', 'volume'])
    # 腾讯 volume 是浮点字符串（如 "22352338.000"），先转 float 再 int
    df['volume'] = df['volume'].astype(float).astype(int)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df


def main():
    print("=" * 60)
    print("📊 ETF 数据增量更新（core 池，腾讯源）")
    print("=" * 60)

    core_codes = get_core_etfs()
    print(f"📌 core 池: {len(core_codes)} 只")
    print(f"⏱️  预计耗时: {len(core_codes) * INTERVAL:.0f} 秒\n")

    writer = DataWriter(db_path=str(PROJECT_ROOT / 'data' / 'etf.db'))

    success = 0
    failed = []

    for i, code in enumerate(core_codes, 1):
        try:
            df = fetch_tencent(code)
            if df.empty:
                print(f"[{i:2d}/{len(core_codes)}] {code}: ✗ 空响应")
                failed.append(code)
                continue

            written = writer.write_daily(code, df, source='tencent')
            new_latest = writer.get_latest_date(code)
            print(f"[{i:2d}/{len(core_codes)}] {code}: ✅ +{written} 条 | 最新 {new_latest}")
            success += 1

            if i < len(core_codes):
                time.sleep(INTERVAL)

        except Exception as e:
            print(f"[{i:2d}/{len(core_codes)}] {code}: ❌ {type(e).__name__}: {str(e)[:50]}")
            failed.append(code)
            time.sleep(INTERVAL)

    print(f"\n{'=' * 60}")
    print(f"✅ 成功: {success}/{len(core_codes)}")
    if failed:
        print(f"❌ 失败: {failed}")

    conn = sqlite3.connect(PROJECT_ROOT / 'data' / 'etf.db')
    cur = conn.cursor()
    cur.execute("SELECT MAX(date), COUNT(DISTINCT code) FROM daily")
    latest, cnt = cur.fetchone()
    conn.close()
    print(f"📅 数据库最新日期: {latest} | 覆盖 ETF: {cnt} 只")


if __name__ == '__main__':
    main()