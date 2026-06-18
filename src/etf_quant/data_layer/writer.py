"""
统一数据写入器
所有数据写入必须经过此模块
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging

from etf_quant.data_layer.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DataWriter:
    """
    统一数据写入器
    
    职责：
    1. 写入 SQLite（唯一）
    2. 事务管理
    3. 增量更新（只写入新数据）
    4. 防重复写入
    
    使用方式：
        from src.data.writer import DataWriter
        
        writer = DataWriter()
        df = pd.DataFrame({...})
        count = writer.write_daily('510300', df)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: 数据库路径，默认使用 etf_data_live/etf.db
        """
        if db_path is None:
            # 使用相对路径
            self.db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'etf_data_live',
                'etf.db'
            )
        else:
            self.db_path = db_path
        
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表结构存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # daily 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL, high REAL, low REAL,
                close REAL, volume INTEGER, amount REAL,
                source TEXT DEFAULT 'tencent',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(code, date)
            )
        ''')
        
        # 索引
        conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_code ON daily(code)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily(date)')
        
        # stock_info 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                code TEXT PRIMARY KEY,
                name TEXT,
                exchange TEXT,
                category TEXT DEFAULT 'ETF',
                status TEXT DEFAULT 'active',
                list_date TEXT,
                delist_date TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
        ''')
        
        # realtime_cache 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS realtime_cache (
                code TEXT PRIMARY KEY,
                name TEXT, price REAL, change REAL, change_pct REAL,
                volume REAL, amount REAL, timestamp TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def write_daily(
        self,
        code: str,
        df: pd.DataFrame,
        source: str = 'tencent'
    ) -> int:
        """
        写入日线数据（增量更新）
        
        Args:
            code: 证券代码（无前缀，如 '510300'）
            df: 日线数据 DataFrame
                必须包含列: date, open, high, low, close, volume
                date格式: YYYY-MM-DD
            source: 数据来源标识
        
        Returns:
            int: 实际写入的记录数
        
        Raises:
            DataValidationError: 数据格式校验失败
        """
        # 数据校验
        errors = self._validate_daily(code, df)
        if errors:
            raise DataValidationError(f"数据校验失败: {len(errors)} 个错误", errors)
        
        # 增量写入
        conn = sqlite3.connect(self.db_path, timeout=30)
        # 启用 WAL 模式，提高并发性能
        conn.execute('PRAGMA journal_mode=WAL')
        count = 0
        now = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            date_str = str(row['date'])
            
            # 检查是否已存在（使用复合主键检查，不依赖id列）
            existing = conn.execute(
                'SELECT 1 FROM daily WHERE code=? AND date=?',
                (code, date_str)
            ).fetchone()
            
            if existing:
                # 已存在，更新 updated_at
                conn.execute(
                    'UPDATE daily SET updated_at=? WHERE code=? AND date=?',
                    (now, code, date_str)
                )
            else:
                # 插入新记录
                conn.execute('''
                    INSERT INTO daily (code, date, open, high, low, close, volume, amount, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code, date_str,
                    float(row.get('open', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    float(row.get('close', 0)),
                    int(row.get('volume', 0)),
                    float(row.get('amount', 0)) if 'amount' in row and pd.notna(row.get('amount')) else None,
                    source, now, now
                ))
                count += 1
        
        conn.commit()
        conn.close()
        
        if count > 0:
            logger.debug(f"写入 {code}: {count} 条新记录")
        
        return count
    
    def _validate_daily(self, code: str, df: pd.DataFrame) -> List[Dict]:
        """验证日线数据"""
        errors = []
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # 检查必需列
        for col in required_cols:
            if col not in df.columns:
                errors.append({'code': code, 'field': col, 'error': 'missing column'})
        
        if errors:
            return errors
        
        # 检查数据值
        for i, row in df.iterrows():
            if pd.isna(row['date']) or str(row['date']).strip() == '':
                errors.append({'code': code, 'field': 'date', 'row': i, 'error': 'empty'})
                continue
            
            try:
                open_p = float(row['open'])
                high_p = float(row['high'])
                low_p = float(row['low'])
                close_p = float(row['close'])
                volume_p = int(row['volume'])
            except (ValueError, TypeError):
                errors.append({'code': code, 'field': 'price', 'row': i, 'error': 'invalid number'})
                continue
            
            if open_p <= 0:
                errors.append({'code': code, 'field': 'open', 'row': i, 'value': open_p, 'error': 'must be > 0'})
            if close_p <= 0:
                errors.append({'code': code, 'field': 'close', 'row': i, 'value': close_p, 'error': 'must be > 0'})
            if high_p < max(open_p, close_p):
                errors.append({'code': code, 'field': 'high', 'row': i, 'error': 'must be >= max(open, close)'})
            if low_p > min(open_p, close_p):
                errors.append({'code': code, 'field': 'low', 'row': i, 'error': 'must be <= min(open, close)'})
            if volume_p < 0:
                errors.append({'code': code, 'field': 'volume', 'row': i, 'value': volume_p, 'error': 'must be >= 0'})
        
        return errors
    
    def write_daily_batch(
        self,
        records: Dict[str, pd.DataFrame]
    ) -> Dict[str, int]:
        """
        批量写入多只ETF的日线数据
        
        Args:
            records: {code: DataFrame, ...}
        
        Returns:
            Dict[str, int]: {code: count, ...}
        """
        results = {}
        for code, df in records.items():
            try:
                count = self.write_daily(code, df)
                results[code] = count
            except DataValidationError as e:
                logger.warning(f"写入 {code} 失败: {e}")
                results[code] = 0
        
        total = sum(results.values())
        logger.info(f"批量写入完成: {len(results)} 只ETF, {total} 条记录")
        
        return results
    
    def write_realtime(
        self,
        code: str,
        quote
    ) -> bool:
        """
        写入实时报价（缓存用）
        
        Args:
            code: 证券代码
            quote: RealtimeQuote 对象或字典
        
        Returns:
            bool: 写入是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            now = datetime.now().isoformat()
            
            if isinstance(quote, dict):
                price = quote.get('price', 0)
                change = quote.get('change', 0)
                change_pct = quote.get('change_pct', 0)
                volume = quote.get('volume', 0)
                amount = quote.get('amount', 0)
                name = quote.get('name', '')
                timestamp = quote.get('timestamp', now)
            else:
                price = getattr(quote, 'price', 0)
                change = getattr(quote, 'change', 0)
                change_pct = getattr(quote, 'change_pct', 0)
                volume = getattr(quote, 'volume', 0)
                amount = getattr(quote, 'amount', 0)
                name = getattr(quote, 'name', '')
                timestamp = getattr(quote, 'timestamp', now)
            
            conn.execute('''
                INSERT OR REPLACE INTO realtime_cache 
                (code, name, price, change, change_pct, volume, amount, timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, price, change, change_pct, volume, amount, timestamp, now))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"写入实时报价失败: {code}, error: {e}")
            return False
    
    def write_stock_info(
        self,
        code: str,
        info: Dict
    ) -> bool:
        """
        写入/更新证券基本信息
        
        Args:
            code: 证券代码
            info: 基本信息字典 {name, exchange, category, ...}
        
        Returns:
            bool: 写入是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            now = datetime.now().isoformat()
            
            conn.execute('''
                INSERT OR REPLACE INTO stock_info 
                (code, name, exchange, category, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                code,
                info.get('name', ''),
                info.get('exchange', ''),
                info.get('category', 'ETF'),
                info.get('status', 'active'),
                now
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"写入证券信息失败: {code}, error: {e}")
            return False
    
    def get_record_count(self, code: str = None) -> int:
        """获取记录数"""
        conn = sqlite3.connect(self.db_path)
        if code:
            cur = conn.execute('SELECT COUNT(*) FROM daily WHERE code=?', (code,))
        else:
            cur = conn.execute('SELECT COUNT(*) FROM daily')
        count = cur.fetchone()[0]
        conn.close()
        return count
    
    def get_latest_date(self, code: str = None) -> str:
        """获取最新日期"""
        conn = sqlite3.connect(self.db_path)
        if code:
            cur = conn.execute('SELECT MAX(date) FROM daily WHERE code=?', (code,))
        else:
            cur = conn.execute('SELECT MAX(date) FROM daily')
        result = cur.fetchone()[0]
        conn.close()
        return result