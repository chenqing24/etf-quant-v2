#!/usr/bin/env python3
"""
60min K 线采集服务（v2）

按 D-005 决策：
- 数据源：主用 B（akshare）+ 备用 A（ifzq.gtimg.cn）
- 容错：单源失败 → 自动切换另一源
- 串行访问：禁止并发（避免触发限流/封 IP）
- 随机停顿：2-5 秒（避免规律请求被识别为爬虫）

调研结果（2026-06-25，按规则 12 先调研再实现）：
- 腾讯 ifzq.gtimg.cn 的 m60 接口对 ETF 返回"股票数据不存在" → **不可用**
- akshare stock_zh_a_minute(symbol='sh515050', period='60') 可用 → **1970 行/2 年**
  - 官方文档：https://akshare.akfamily.xyz/data/stock/stock.html
  - period 支持 '1', '5', '15', '30', '60'
- 决策：akshare 做主源，腾讯留作日线（已稳定）

被谁调用：
- skills/etf-daily/scripts/run_daily.py（每日 14:30 增量更新）
- 一次性历史回填：python scripts/fetch_60min_data.py --history

SOUL.md 规则遵守：
- 规则 16: 数据源统一 SQLite（不直接 CSV）
- 规则 29: 数据接入必文档先行
- 规则 12: 先调研再实现（✅ 已调研 akshare 官方文档）
"""
import sys
import time
import random
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import requests
import pandas as pd

# 走 DataWriter（按规则 15：业务代码禁止直接 DB 连接）
from etf_quant.data_layer.writer import DataWriter

# logging 配置（Google Python Style Guide 推荐）
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ==== 1. 数据源配置 ====
# 主源：akshare（已验证 60min 可用）
# 备用：腾讯 ifzq.gtimg.cn（60min 对 ETF 不可用，留作日线）
TENCENT_URL = 'http://ifzq.gtimg.cn/appstock/app/fqkline/get'
TENCENT_60MIN_PARAM_FMT = '{symbol},m60,,,320,qfq'

AKSHARE_AVAILABLE = False
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    pass

# ==== 2. 串行 + 随机停顿 ====
def polite_sleep(min_sec: float = 2.0, max_sec: float = 5.0):
    """随机停顿 2-5 秒（避免规律请求）"""
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)


# ==== 3. 主源：腾讯 ifzq.gtimg.cn ====
def fetch_tencent_60min(code: str, n: int = 320) -> Optional[pd.DataFrame]:
    """
    腾讯 60min K 线

    接口：http://ifzq.gtimg.cn/appstock/app/fqkline/get
    参数：param={symbol},m60,,,320,qfq（m60 = 60 分钟）
    返回：date, open, close, high, low, volume
    """
    if code.startswith('5') or code.startswith('6'):
        symbol = f'sh{code}'
    elif code.startswith('1'):
        symbol = f'sz{code}'
    else:
        symbol = f'sz{code}'

    try:
        r = requests.get(
            TENCENT_URL,
            params={'param': TENCENT_60MIN_PARAM_FMT.format(symbol=symbol), '_var': 'kline_m60qfq'},
            timeout=15,
        )
        r.raise_for_status()
        text = r.text.lstrip('kline_m60qfq=').strip()
        if not text:
            return None
        payload = json.loads(text)
        if payload.get('code') != 0:
            return None
        data = payload.get('data', {}).get(symbol)
        if not data:
            return None
        # 60min 数据可能在 'm60' 字段（先看 m60，没有则降级到 day）
        rows = data.get('m60') or data.get('qfqday') or data.get('day')
        if not rows:
            return None

        records = []
        for row in rows:
            if len(row) < 6:
                continue
            records.append({
                'code': code,
                'datetime': row[0],
                'open': float(row[1]),
                'close': float(row[2]),
                'high': float(row[3]),
                'low': float(row[4]),
                'volume': float(row[5]),
                'source': 'tencent_60min',
            })
        return pd.DataFrame(records)
    except Exception as e:
        print(f'  ⚠ 腾讯 60min [{code}] 失败: {e}')
        return None


# ==== 4. 备用源：akshare ====
def fetch_akshare_60min(code: str, adjust: str = 'qfq') -> Optional[pd.DataFrame]:
    """
    akshare 60min K 线（主源，2026-06-25 实测可用）

    接口：ak.stock_zh_a_minute(symbol='sh515050', period='60', adjust='qfq')
    注意：symbol 必须带 sh/sz 前缀，否则失败
    官方文档：https://akshare.akfamily.xyz/data/stock/stock.html

    Args:
        code: ETF 代码（不带前缀）
        adjust: 复权方式（qfq=前复权，默认 / hfq=后复权 / 空=不复权）
    """
    if not AKSHARE_AVAILABLE:
        return None
    # 加 sh/sz 前缀
    if code.startswith('5') or code.startswith('6'):
        symbol = f'sh{code}'
    else:
        symbol = f'sz{code}'
    try:
        df = ak.stock_zh_a_minute(symbol=symbol, period='60', adjust=adjust)
        if df is None or df.empty:
            return None
        # akshare 列名规范化：day, open, close, high, low, volume
        df = df.rename(columns={'day': 'datetime'})
        # 【D-006 修复】成交量单位修正：akshare 返回"股"，日线是"手"
        # 实测：6/23 比值 100.00x, 6/24 比值 100.00x（精确 100 倍）
        # 修正：volume ÷ 100（股 → 手）
        df['volume'] = df['volume'].astype(float) / 100.0
        df['code'] = code
        df['source'] = 'akshare_60min'
        return df[['code', 'datetime', 'open', 'close', 'high', 'low', 'volume', 'source']]
    except Exception as e:
        print(f'  ⚠ akshare 60min [{code}] 失败: {type(e).__name__}: {str(e)[:60]}')
        return None


# ==== 5. 多源带回退的采集器 ====
def fetch_60min_with_fallback(code: str, n: int = 320) -> Tuple[Optional[pd.DataFrame], str]:
    """
    优先 akshare（已验证），失败后用腾讯

    Returns: (dataframe, source_used)
    """
    # 主源：akshare（60min 已验证可用）
    df = fetch_akshare_60min(code)
    if df is not None and not df.empty:
        return df, 'akshare'

    # 备用源：腾讯
    df = fetch_tencent_60min(code, n)
    if df is not None and not df.empty:
        return df, 'tencent'

    return None, 'failed'


# ==== 6. 主流程：14 ETF 串行采集（走 DataWriter，按规则 15） ====
def fetch_all_etfs_60min(db_path: Path, codes: Optional[list] = None) -> dict:
    """
    串行采集所有 core ETF 的 60min 数据（走 DataWriter，按规则 15）

    Returns: {code: (rows_added, source_used)}
    """
    if codes is None:
        # 用 ETFListLoader 而非直连（按规则 15）
        from etf_quant.universe.loader import ETFListLoader
        pool = ETFListLoader().get_core_pool()
        codes = [p.code for p in pool]

    print(f'=== 60min 采集 ===')
    print(f'  ETF 数量: {len(codes)}')
    print(f'  策略: 优先 akshare, 失败→腾讯')
    print(f'  间隔: 2-5 秒随机停顿')
    print(f'  串行: 不并发')
    print(f'  写入: DataWriter.write_60min()（按规则 15）')
    print()

    writer = DataWriter(db_path=str(db_path))

    results = {}
    for i, code in enumerate(codes, 1):
        print(f'[{i}/{len(codes)}] {code} ...', end=' ', flush=True)
        df, source = fetch_60min_with_fallback(code)
        if df is not None and not df.empty:
            try:
                n_added = writer.write_60min(code, df, source=f'{source}_60min')
                print(f'✅ +{n_added} 条 ({source})')
                results[code] = (n_added, source)
            except Exception as e:
                logger.error(f'写入 {code} 失败: {type(e).__name__}: {e}')
                print(f'❌ 写入失败: {e}')
                results[code] = (0, source)
        else:
            print(f'❌ 双源失败')
            results[code] = (0, 'failed')

        # 最后一个不 sleep
        if i < len(codes):
            polite_sleep()

    return results


# ==== 8. CLI ====
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='60min K 线采集服务（主用腾讯，备用 akshare）')
    parser.add_argument('--db', default=str(PROJECT_ROOT / 'data' / 'etf.db'), help='数据库路径')
    parser.add_argument('--codes', nargs='+', default=None, help='指定 ETF 代码（默认 core 池）')
    parser.add_argument('--test', action='store_true', help='只测试 1 只 ETF（515050）')
    args = parser.parse_args()

    db_path = Path(args.db)
    codes = ['515050'] if args.test else args.codes

    if args.test:
        print('=== 测试模式：单只 ETF 515050 ===\n')
        df, src = fetch_60min_with_fallback('515050')
        if df is not None:
            print(f'✅ 来源: {src}')
            print(f'   行数: {len(df)}')
            print(f'   时间范围: {df["datetime"].iloc[0]} ~ {df["datetime"].iloc[-1]}')
            print(f'   列: {list(df.columns)}')
            print(f'\n   前 5 行:')
            print(df.head().to_string(index=False))
            print(f'\n   后 5 行:')
            print(df.tail().to_string(index=False))
            # 走 DataWriter 写入
            print(f'\n   写入数据库（DataWriter.write_60min）...')
            writer = DataWriter(db_path=str(db_path))
            count = writer.write_60min('515050', df, source=f'{src}_60min')
            print(f'   ✅ 新增 {count} 条到 {db_path}')
        else:
            print('❌ 双源都失败')
    else:
        results = fetch_all_etfs_60min(db_path, codes)
        print(f'\n=== 采集完成 ===')
        total = sum(r[0] for r in results.values())
        success = sum(1 for r in results.values() if r[1] != 'failed')
        print(f'  成功: {success}/{len(results)} 只')
        print(f'  总新增: {total} 条')
        if success < len(results):
            failed = [c for c, r in results.items() if r[1] == 'failed']
            print(f'  失败: {failed}')