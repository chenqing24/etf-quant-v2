#!/usr/bin/env python3
"""
数据契约定义
================
每个模块的输入/输出必须符合此契约。

【契约层级】
1. 数据契约：DataFrame 的字段/类型/约束
2. 接口契约：公共方法的 (输入, 输出) 签名

【变更规范】
- 契约变更需在 CHANGELOG.md 记录
- 破坏性变更需 major 版本升级
- 新增字段向后兼容

【使用方式】
from etf_quant.data_layer.contracts import OHLCVSchema, IndicatorSchema

errors = OHLCVSchema.validate(df, source="fetcher")
if errors:
    raise ContractViolation(errors)
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Set, Optional, Any, Protocol, runtime_checkable


# ══════════════════════════════════════════════════════════════
# 数据契约层
# ══════════════════════════════════════════════════════════════

class OHLCVSchema:
    """K线数据契约（OHLCV）
    
    【来源】
    - SQLite daily 表
    - 腾讯实时 API
    - CSV 文件（历史兼容）
    
    【下游消费方】
    - Indicator.calculate()
    - Selector.select_etfs()
    - ReportGenerator
    
    【字段规范】
    ┌─────────┬────────┬───────────────────────────────────┐
    │ 字段     │ 类型    │ 约束                               │
    ├─────────┼────────┼───────────────────────────────────┤
    │ code    │ str    │ 非空，6位数字代码                  │
    │ date    │ str    │ YYYY-MM-DD 格式                    │
    │ open    │ float  │ > 0                                │
    │ high    │ float  │ >= low, > 0                        │
    │ low     │ float  │ <= high, > 0                       │
    │ close   │ float  │ >= low, <= high, > 0               │
    │ volume  │ int    │ >= 0                               │
    └─────────┴────────┴───────────────────────────────────┘
    """
    
    REQUIRED_COLUMNS = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
    
    @classmethod
    def validate(cls, df: pd.DataFrame, source: str = "") -> List[str]:
        """验证 DataFrame 是否符合 OHLCV 契约
        
        Args:
            df: 待验证数据
            source: 来源标识（用于错误信息）
            
        Returns:
            错误列表，空=通过
        """
        errors = []
        
        # 1. 检查必需列
        missing = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            errors.append(f"[{source}] 缺少必需列: {missing}")
        
        # 2. 日期格式
        if 'date' in df.columns:
            invalid = df[~df['date'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')]
            if len(invalid) > 0:
                errors.append(f"[{source}] 存在日期格式错误（需 YYYY-MM-DD）")
        
        # 3. 价格正数
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors='coerce')
                if vals.isna().sum() > 0:
                    errors.append(f"[{source}] {col} 存在非数值")
                elif (vals <= 0).sum() > 0:
                    errors.append(f"[{source}] {col} 存在非正值")
        
        # 4. 业务约束: high >= low
        if 'high' in df.columns and 'low' in df.columns:
            high_val = pd.to_numeric(df['high'], errors='coerce')
            low_val = pd.to_numeric(df['low'], errors='coerce')
            invalid = high_val < low_val
            if invalid.sum() > 0:
                errors.append(f"[{source}] 存在 high < low 的异常数据")
        
        # 5. 业务约束: close ∈ [low, high]
        if all(c in df.columns for c in ['close', 'high', 'low']):
            high_val = pd.to_numeric(df['high'], errors='coerce')
            low_val = pd.to_numeric(df['low'], errors='coerce')
            close_val = pd.to_numeric(df['close'], errors='coerce')
            invalid = (close_val > high_val) | (close_val < low_val)
            if invalid.sum() > 0:
                errors.append(f"[{source}] 存在 close 超出 [low, high] 范围的数据")
        
        return errors


class IndicatorSchema:
    """指标计算输出契约
    
    【输入】
    - 符合 OHLCVSchema 的 DataFrame
    
    【输出】
    - 在 OHLCV 基础上新增以下字段
    
    【字段规范】
    ┌────────────┬────────┬───────────────────────────────────┐
    │ 字段       │ 类型   │ 说明                               │
    ├────────────┼────────┼───────────────────────────────────┤
    │ ma5        │ float  │ 5日均线                           │
    │ ma10       │ float  │ 10日均线                          │
    │ ma20       │ float  │ 20日均线                          │
    │ ma60       │ float  │ 60日均线                          │
    │ ma120      │ float  │ 120日均线                         │
    │ ma_vol_20  │ float  │ 20日成交量均线                    │
    │ vol_ratio  │ float  │ 量比 (volume / ma_vol_20)        │
    │ rsi_5      │ float  │ 5日RSI，范围 [0, 100]            │
    │ rsi_14     │ float  │ 14日RSI，范围 [0, 100]           │
    └────────────┴────────┴───────────────────────────────────┘
    """
    
    REQUIRED_COLUMNS = ['ma5', 'ma10', 'ma20', 'ma60', 'ma120', 
                        'ma_vol_20', 'vol_ratio', 'rsi_5', 'rsi_14']
    
    # OHLCV 列必须保留
    OHLCV_COLUMNS = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
    
    @classmethod
    def validate(cls, df: pd.DataFrame, source: str = "") -> List[str]:
        """验证指标数据契约"""
        errors = []
        
        # 1. 检查指标列
        missing = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            errors.append(f"[{source}] 缺少指标列: {missing}")
        
        # 2. RSI 范围验证
        for col in ['rsi_5', 'rsi_14']:
            if col in df.columns:
                invalid = (df[col] < 0) | (df[col] > 100)
                if invalid.sum() > 0:
                    errors.append(f"[{source}] {col} 超出 [0, 100] 范围")
        
        # 3. 检查 OHLCV 列是否保留
        for col in cls.OHLCV_COLUMNS:
            if col in df.columns and col not in cls.REQUIRED_COLUMNS:
                continue  # OHLCV 列是额外的
            if col not in df.columns and col in cls.OHLCV_COLUMNS:
                errors.append(f"[{source}] 缺少原始 OHLCV 列: {col}")
        
        return errors


class SelectorResultSchema:
    """选股结果契约
    
    【输入】
    - data: Dict[str, pd.DataFrame]
      - key: ETF代码（str）
      - value: 符合 OHLCVSchema 或 IndicatorSchema 的 DataFrame
    - config: StrategyConfig
      - train_start: str (YYYY-MM-DD)
      - train_end: str (YYYY-MM-DD)
      - top_n: int
      - exclude_codes: Set[str]
    
    【输出】
    - Set[str]，选中的 ETF 代码集合
    
    【约束】
    - 返回的代码必须在输入的 keys 中
    - 返回数量 <= config.top_n
    """
    
    @classmethod
    def validate(cls, result: Set[str], input_keys: Set[str],
                 max_count: Optional[int] = None) -> List[str]:
        """验证选股结果契约"""
        errors = []
        
        # 1. 检查返回代码是否在输入中
        invalid_codes = result - input_keys
        if invalid_codes:
            errors.append(f"返回的代码不在输入中: {invalid_codes}")
        
        # 2. 检查数量限制
        if max_count is not None and len(result) > max_count:
            errors.append(f"返回数量 {len(result)} 超过限制 {max_count}")
        
        return errors


class TradeRecordSchema:
    """交易记录契约
    
    【字段规范】
    ┌──────────┬────────┬───────────────────────────────────┐
    │ 字段     │ 类型   │ 说明                               │
    ├──────────┼────────┼───────────────────────────────────┤
    │ code     │ str    │ ETF代码                           │
    │ name     │ str    │ ETF名称                           │
    │ action   │ str    │ buy/sell                          │
    │ price    │ float  │ 成交价格，> 0                      │
    │ quantity │ int    │ 成交数量，> 0                      │
    │ amount   │ float  │ 成交金额，= price * quantity       │
    │ date     │ str    │ 交易日期 YYYY-MM-DD               │
    │ reason   │ str    │ 交易原因                          │
    └──────────┴────────┴───────────────────────────────────┘
    """
    
    REQUIRED_COLUMNS = ['code', 'action', 'price', 'quantity', 'date']
    VALID_ACTIONS = {'buy', 'sell'}
    
    @classmethod
    def validate(cls, df: pd.DataFrame, source: str = "") -> List[str]:
        """验证交易记录契约"""
        errors = []
        
        # 1. 检查必需列
        missing = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            errors.append(f"[{source}] 缺少必需列: {missing}")
        
        # 2. 验证 action 值
        if 'action' in df.columns:
            invalid = ~df['action'].isin(cls.VALID_ACTIONS)
            if invalid.sum() > 0:
                errors.append(f"[{source}] action 存在非法值，仅支持 {cls.VALID_ACTIONS}")
        
        # 3. 验证金额计算
        if all(c in df.columns for c in ['price', 'quantity', 'amount']):
            calc_amount = df['price'] * df['quantity']
            diff = (calc_amount - df['amount']).abs()
            if (diff > 0.01).sum() > 0:
                errors.append(f"[{source}] amount ≠ price * quantity")
        
        return errors


# ══════════════════════════════════════════════════════════════
# 接口契约层（Protocol）
# ══════════════════════════════════════════════════════════════

@runtime_checkable
class DataLoaderProtocol(Protocol):
    """DataLoader 接口契约
    
    【输入】
    - db_path: str（可选，默认使用 DATA_DIR/DB_NAME）
    - min_rows: int（默认 300）
    
    【输出】
    - Dict[str, pd.DataFrame]
      - key: ETF代码（str）
      - value: 符合 OHLCVSchema 的 DataFrame
    
    【约束】
    - date 列按 ASC 排序
    - 过滤掉行数 < min_rows 的 ETF
    """
    
    def load(self, min_rows: int = 300) -> Dict[str, pd.DataFrame]: ...
    
    def load_single(self, code: str, min_rows: int = 1) -> Optional[pd.DataFrame]: ...
    
    def get_date_range(self, code: str = None) -> Dict[str, str]: ...


@runtime_checkable
class IndicatorProtocol(Protocol):
    """Indicator 接口契约
    
    【输入】
    - df: pd.DataFrame，符合 OHLCVSchema
    
    【输出】
    - pd.DataFrame，符合 IndicatorSchema（在输入基础上新增指标列）
    """
    
    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame: ...
    
    @staticmethod
    def calculate_all(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]: ...

@runtime_checkable
class SelectorProtocol(Protocol):
    """Selector 接口契约
    
    【输入】
    - data: Dict[str, pd.DataFrame]，每个 DataFrame 符合 IndicatorSchema
    - config: Any（StrategyConfig）
    
    【输出】
    - Set[str]，选中的 ETF 代码
    """
    
    def select_etfs(self, data: Dict[str, pd.DataFrame], 
                   config: Any) -> Set[str]: ...


@runtime_checkable
class ReportGeneratorProtocol(Protocol):
    """ReportGenerator 接口契约
    
    【输入】
    - data: Dict[str, pd.DataFrame]，每个 DataFrame 符合 IndicatorSchema
    - config: Any
      - capital: float，投资本金
    
    【输出】
    - str，Markdown 格式的决策报告
    
    【约束】
    - 报告必须包含：今日操作、目标ETF、价格、数量、止损止盈
    """
    
    def generate_report(self, capital: float, **kwargs) -> str: ...

@runtime_checkable
class FetcherProtocol(Protocol):
    """Fetcher 接口契约
    
    【输入】
    - codes: List[str]，ETF 代码列表
    - days: int，采集天数
    
    【输出】
    - Dict[str, pd.DataFrame]
      - key: ETF代码
      - value: 符合 OHLCVSchema 的 DataFrame
    """
    
    def fetch(self, codes: List[str], days: int = 7) -> Dict[str, pd.DataFrame]: ...


# ══════════════════════════════════════════════════════════════
# 契约异常
# ══════════════════════════════════════════════════════════════

class ContractViolation(Exception):
    """契约违反异常"""
    
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"契约违反: {'; '.join(errors)}")


__all__ = [
    'OHLCVSchema',
    'IndicatorSchema', 
    'SelectorResultSchema',
    'TradeRecordSchema',
    'ContractViolation',
    'DataLoaderProtocol',
    'IndicatorProtocol',
    'SelectorProtocol',
    'ReportGeneratorProtocol',
    'FetcherProtocol',
]