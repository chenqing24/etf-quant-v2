#!/usr/bin/env python3
"""
run_real_backtest.py — v2 真实回测入口（替换 run_validate.py 的 mock 数据）

用途：把 v2 28 因子经 Backtesting.py 跑真实回测，输出 Sharpe/MaxDD/Return。
     替换 skills/etf-research/scripts/run_validate.py 的硬编码 mock。

被谁调用：
- 用户手动（教学/散户场景）
- etf-research skill（TODO：注入真实数据）

借鉴业界（按规则 13）：
- Backtesting.py (MIT) 执行引擎
- v1 时代 backtest_v3.py 输出格式（兼容）

用法：
    # 单只
    python3 scripts/run_real_backtest.py single 512170

    # 全部 core 池
    python3 scripts/run_real_backtest.py all

    # 自定义因子
    python3 scripts/run_real_backtest.py single 512170 --factors T1_macd_bar M2_momentum_5d
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
sys.path.insert(0, str(SRC_ROOT))

from etf_quant.backtest.backtesting_adapter import RealBacktestEngine
from etf_quant.universe import ETFListLoader


def get_core_codes() -> list[str]:
    """通过 ETFListLoader 读 core 池（按规则 15：业务代码禁止直接 DB 连接）"""
    loader = ETFListLoader(db_path=str(PROJECT_ROOT / 'data' / 'etf.db'))
    return [e.code for e in loader.get_core_pool()]


def run_single(code: str, factors: list[str] | None) -> dict:
    engine = RealBacktestEngine(factor_names=factors)
    result = engine.run(code=code, db_path=PROJECT_ROOT / 'data' / 'etf.db')
    return {
        'code': result.code,
        'start': result.start,
        'end': result.end,
        'total_return': round(result.total_return, 2),
        'annual_return': round(result.annual_return, 2),
        'sharpe': round(result.sharpe, 2),
        'max_drawdown': round(result.max_drawdown, 2),
        'n_trades': result.n_trades,
        'win_rate': round(result.win_rate, 2),
    }


def main():
    parser = argparse.ArgumentParser(description='v2 真实回测（Backtesting.py）')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_single = sub.add_parser('single', help='单只 ETF 回测')
    p_single.add_argument('code', help='ETF 代码（如 512170）')
    p_single.add_argument('--factors', nargs='+', default=None, help='因子名列表')

    sub.add_parser('all', help='全部 core 池 ETF 回测')

    args = parser.parse_args()

    if args.cmd == 'single':
        result = run_single(args.code, args.factors)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == 'all':
        codes = get_core_codes()
        print(f"📊 跑全部 core 池 {len(codes)} 只...")
        results = []
        for i, code in enumerate(codes, 1):
            try:
                r = run_single(code, None)
                r['status'] = '✅'
                print(f"[{i}/{len(codes)}] {code}: 收益 {r['total_return']}% | Sharpe {r['sharpe']} | 交易 {r['n_trades']} 次")
                results.append(r)
            except Exception as e:
                print(f"[{i}/{len(codes)}] {code}: ❌ {type(e).__name__}: {str(e)[:50]}")
                results.append({'code': code, 'status': '❌', 'error': str(e)[:100]})

        # 汇总
        ok = [r for r in results if r.get('status') == '✅']
        if ok:
            print(f"\n📈 汇总（{len(ok)}/{len(codes)} 成功）:")
            print(f"  平均收益:   {sum(r['total_return'] for r in ok) / len(ok):.2f}%")
            print(f"  平均 Sharpe: {sum(r['sharpe'] for r in ok) / len(ok):.2f}")
            print(f"  平均回撤:   {sum(r['max_drawdown'] for r in ok) / len(ok):.2f}%")
            print(f"  总交易:     {sum(r['n_trades'] for r in ok)} 次")


if __name__ == '__main__':
    main()