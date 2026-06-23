#!/usr/bin/env python3
"""
数据加载器 - 统一数据读取入口

重构说明（v3.0 Phase 2）：
- 只从 SQLite 读取（统一数据源）
- 移除 CSV 读取逻辑
- 与 DataWriter 配合使用
"""
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import logging

import pandas as pd

from etf_quant.config.constants import DB_NAME, DATA_DIR

logger = logging.getLogger(__name__)


# ETF名称加载器 - 从数据库读取真实名称
class ETFNameLoader:
    """ETF名称加载器 - 兼容旧代码"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(DATA_DIR) / DB_NAME)
        self._name_cache: Dict[str, str] = {}
    
    def get_name(self, code: str) -> str:
        """获取ETF名称"""
        if code in self._name_cache:
            return self._name_cache[code]
        
        # 从数据库读取
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute('SELECT name FROM stock_info WHERE code=?', (code,))
            row = cur.fetchone()
            if row:
                name = row[0] or code
            else:
                name = code
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            # L302 教训：精确捕获 SQLite 异常，不吞所有错误
            name = code
        finally:
            conn.close()
        
        self._name_cache[code] = name
        return name
    
    def get_names(self, codes: List[str]) -> Dict[str, str]:
        """批量获取ETF名称"""
        return {code: self.get_name(code) for code in codes}


class DataLoader:
    """
    ETF数据加载器 - 从SQLite读取（唯一数据源）
    
    核心原则：只查 SQLite，不查 CSV
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化加载器
        
        Args:
            db_path: 数据库路径，默认使用 {DATA_DIR}/{DB_NAME}
        """
        self.db_path = db_path or str(Path(DATA_DIR) / DB_NAME)
        self.data: Dict[str, pd.DataFrame] = {}
    
    def load(self, min_rows: int = 300, codes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        加载ETF历史数据（从SQLite）
        
        Args:
            min_rows: 最少行数要求，少于此行数的ETF会被过滤
            codes: 可选，指定只加载这些ETF代码，默认加载全部
            
        Returns:
            {code: DataFrame}
        """
        self.data = {}
        
        if not Path(self.db_path).exists():
            logger.warning(f"数据库文件不存在: {self.db_path}")
            return self.data
        
        try:
            self.data = self._load_from_sqlite(min_rows, codes=codes)
            total_rows = sum(len(df) for df in self.data.values())
            logger.info(f"从SQLite加载 {len(self.data)} 只ETF, 共{total_rows}行")
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            self.data = {}
        
        return self.data
    
    def _load_from_sqlite(self, min_rows: int = 300, db_path: str = None, codes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """从SQLite加载数据
        
        Args:
            min_rows: 最小行数
            db_path: 可选的数据库路径（用于测试覆盖）
            codes: 可选，指定只加载这些ETF代码
        """
        # 支持传入 db_path 或使用实例的 db_path
        effective_path = db_path if db_path is not None else self.db_path
        # 确保是字符串
        effective_path = str(effective_path) if not isinstance(effective_path, str) else effective_path
        
        # 如果传入的是路径而不是 int，说明参数位置被调用方搞混了，忽略 min_rows
        if not isinstance(min_rows, int):
            min_rows = 300
        
        # 检查数据库文件是否存在
        if not Path(effective_path).exists():
            logger.warning(f"数据库文件不存在: {effective_path}")
            return {}
        
        conn = sqlite3.connect(effective_path)
        
        try:
            # 获取ETF代码列表（如果有codes参数则只加载这些）
            if codes:
                target_codes = codes
            else:
                cur = conn.cursor()
                cur.execute('SELECT DISTINCT code FROM daily ORDER BY code')
                target_codes = [r[0] for r in cur.fetchall()]
            
            data = {}
            for code in target_codes:
                # 检查列是否存在
                cur = conn.cursor()
                cur.execute('PRAGMA table_info(daily)')
                cols = [r[1] for r in cur.fetchall()]
                select_cols = ', '.join([c for c in cols if c != 'id'])
                
                df = pd.read_sql(
                    f'SELECT {select_cols} FROM daily WHERE code=? ORDER BY date',
                    conn,
                    params=(code,)
                )
                df = self._process_df(df)
                if len(df) >= min_rows:
                    data[code] = df
            
            return data
        finally:
            conn.close()
    
    def _process_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化处理"""
        # 重命名列（兼容大小写）
        col_mapping = {}
        for c in df.columns:
            if c.lower() in ('date',):
                col_mapping[c] = 'date'
            elif c.lower() in ('vol', 'volume'):
                col_mapping[c] = 'volume'
            elif c.lower() in ('open', 'high', 'low', 'close', 'amount'):
                col_mapping[c] = c.lower()
        
        if col_mapping:
            df = df.rename(columns=col_mapping)
        
        # 转换数据类型
        df['date'] = df['date'].astype(str)
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        if 'open' in df.columns:
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
        if 'high' in df.columns:
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
        if 'low' in df.columns:
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
        
        # 按日期排序
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def load_single(self, code: str, min_rows: int = 1) -> Optional[pd.DataFrame]:
        """
        加载单个ETF数据
        
        Args:
            code: ETF代码（如 '510300'）
            min_rows: 最少行数要求
            
        Returns:
            DataFrame 或 None
        """
        if not Path(self.db_path).exists():
            return None
        
        # 确保 db_path 是字符串
        db_path = str(self.db_path) if not isinstance(self.db_path, str) else self.db_path
        conn = sqlite3.connect(db_path)
        
        try:
            # 检查列是否存在
            cur = conn.execute('PRAGMA table_info(daily)')
            cols = [r[1] for r in cur.fetchall()]
            select_cols = ', '.join([c for c in cols if c != 'id'])
            
            df = pd.read_sql(
                f'SELECT {select_cols} FROM daily WHERE code=? ORDER BY date',
                conn,
                params=(code,)
            )
            df = self._process_df(df)
            
            if len(df) >= min_rows:
                return df
            return None
        finally:
            conn.close()
    
    def get_etf_list(self) -> List[str]:
        """获取已存储的ETF代码列表"""
        if not Path(self.db_path).exists():
            return []
        
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute('SELECT DISTINCT code FROM daily ORDER BY code')
            return [r[0] for r in cur.fetchall()]
        finally:
            conn.close()
    
    def get_latest_date(self, code: str = None) -> Optional[str]:
        """获取最新日期"""
        if not Path(self.db_path).exists():
            return None
        
        conn = sqlite3.connect(self.db_path)
        try:
            if code:
                cur = conn.execute('SELECT MAX(date) FROM daily WHERE code=?', (code,))
            else:
                cur = conn.execute('SELECT MAX(date) FROM daily')
            result = cur.fetchone()[0]
            return result
        finally:
            conn.close()
    
    def get_record_count(self, code: str = None) -> int:
        """获取记录数"""
        if not Path(self.db_path).exists():
            return 0
        
        conn = sqlite3.connect(self.db_path)
        try:
            if code:
                cur = conn.execute('SELECT COUNT(*) FROM daily WHERE code=?', (code,))
            else:
                cur = conn.execute('SELECT COUNT(*) FROM daily')
            return cur.fetchone()[0]
        finally:
            conn.close()
    
    def get_date_range(self, code: str = None) -> Dict[str, str]:
        """获取日期范围"""
        if not Path(self.db_path).exists():
            return {}
        
        conn = sqlite3.connect(self.db_path)
        try:
            if code:
                cur = conn.execute(
                    'SELECT MIN(date), MAX(date) FROM daily WHERE code=?',
                    (code,)
                )
            else:
                cur = conn.execute('SELECT MIN(date), MAX(date) FROM daily')
            result = cur.fetchone()
            return {'min_date': result[0], 'max_date': result[1]}
        finally:
            conn.close()


# 兼容旧代码
def load_etf_data(min_rows: int = 300) -> Dict[str, pd.DataFrame]:
    """加载ETF数据（便捷函数）"""
    loader = DataLoader()
    return loader.load(min_rows)


if __name__ == '__main__':
    loader = DataLoader()
    data = loader.load(min_rows=300)
    print(f"加载了 {len(data)} 只ETF")
    
    if data:
        for code, df in list(data.items())[:3]:
            print(f"  {code}: {len(df)} 行, {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}")


__all__ = ['DataLoader', 'load_etf_data']