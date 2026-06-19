#!/usr/bin/env python3
"""
ETF 池 Repository（v1 US-001 继承，v2 落地）

用途：
    v1 单一数据源（从 etf.db.etf_names 表读取 ETF 池）。
    v2 在 data_layer 复用：5 角色过滤（core / reference / excluded /
    legacy_holding / unclassified）+ tradable 过滤。

被谁调用：
    - src/etf_quant/execution/tracker.py（v1 兼容）
    - src/etf_quant/data_layer/etf_pool_loader.py（v1 兼容）
    - 未来：src/etf_quant/universe/loader.py（v2 重新设计）

功能说明：
    - 封装 SQL 访问，调用方无需关心表名/字段名
    - 支持按 pool_role + tradable 过滤
    - v2 继承 + v1 真实 SQL（不重写）

使用方式：
    from etf_quant.data_layer.etf_pool_repository import ETFRepository
    repo = ETFRepository(db_path="/path/etf.db")
    codes = repo.list_codes(role="core", tradable_only=True)

依赖：
    - sqlite3：直接 SQL（data_layer 豁免规则 15）
    - schema/migrations/003_add_tradable_pool_role.sql
    - schema/migrations/005_add_is_reference.sql

注意事项：
    - v1 US-002 状态：tradable/pool_role 字段已加（schema 003）
    - list_codes(role=...) 现在按 role 过滤
    - 不传 role 返回全部（1486 条）
    - tradable_only=True 过滤可交易 ETF（默认 False）
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Literal

_logger = logging.getLogger(__name__)

PoolRole = Literal['core', 'reference', 'excluded']


class ETFRepository:
    """ETF 元数据 + 池访问入口（单一数据源）"""

    def is_tradable(self, code: str) -> bool:
        """检查 code 是否在池中且可交易（v2 schema 003）。"""
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    "SELECT 1 FROM etf_names WHERE code = ? AND tradable = 1",
                    (code,),
                )
                return cur.fetchone() is not None
        except Exception as e:
            _logger.error(f"ETFRepository.is_tradable 失败: {e}")
            return False

    DEFAULT_DB = 'etf_data_live/etf.db'

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DEFAULT_DB

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ===== 池接口（按角色）=====

    def list_codes(self, role: PoolRole = 'core') -> List[str]:
        """
        返回指定角色的纯数字代码列表（无 sh/sz 前缀）

        US-002 完成：etf_names 现在有 pool_role 字段，
        会按 tradable/pool_role 过滤。
        """
        sql, params = self._build_list_codes_sql(role)
        try:
            with self._conn() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [r[0] for r in rows]
        except Exception as e:
            _logger.error(f"ETFRepository.list_codes 失败: {e}")
            return []

    def list_with_meta(self, role: PoolRole = 'core') -> List[dict]:
        """返回 code + name + exchange + aum 的字典列表"""
        sql, params = self._build_list_with_meta_sql(role)
        try:
            with self._conn() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            _logger.error(f"ETFRepository.list_with_meta 失败: {e}")
            return []

    def all_codes(self) -> List[str]:
        """所有 ETF 代码（1486 条，不分角色）"""
        try:
            with self._conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT code FROM etf_names")
                return [r[0] for r in cur.fetchall()]
        except Exception as e:
            _logger.error(f"ETFRepository.all_codes 失败: {e}")
            return []

    # ===== 元数据接口 =====

    def get_name(self, code: str) -> Optional[str]:
        """根据 code 查 name"""
        try:
            with self._conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM etf_names WHERE code = ?", (code,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            _logger.error(f"ETFRepository.get_name 失败: {e}")
            return None

    def get_meta(self, code: str) -> Optional[dict]:
        """根据 code 查全部元数据

        US-002 之后: 包含 tradable + pool_role
        US-001 阶段: 不包含（按需 fallback）
        """
        cols = self._get_etf_names_columns()
        # 基础字段
        base_cols = ['code', 'name', 'name_sina', 'exchange', 'category',
                     'tracking_index', 'aum', 'verified', 'updated_at']
        # US-002 字段
        if 'tradable' in cols:
            base_cols.append('tradable')
        if 'pool_role' in cols:
            base_cols.append('pool_role')
        cols_str = ', '.join(base_cols)
        try:
            with self._conn() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    f"SELECT {cols_str} FROM etf_names WHERE code = ?",
                    (code,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            _logger.error(f"ETFRepository.get_meta 失败: {e}")
            return None

    # ===== 写入接口（管理用）=====

    def upsert_name(self, code: str, name: str, **kwargs) -> bool:
        """
        插入或更新 ETF 元数据

        Args:
            code: ETF 代码
            name: ETF 名称（同时插入和更新）
            **kwargs: 其他字段（exchange, aum, category, tracking_index, name_sina）

        Returns:
            True 成功, False 失败
        """
        allowed = {'name_sina', 'exchange', 'category', 'tracking_index', 'aum'}
        extra_cols = {k: v for k, v in kwargs.items() if k in allowed}
        try:
            with self._conn() as conn:
                cur = conn.cursor()
                if extra_cols:
                    cols = ['code', 'name'] + list(extra_cols.keys())
                    placeholders = ', '.join(['?'] * len(cols))
                    values = [code, name] + list(extra_cols.values())
                    cur.execute(
                        f"INSERT OR REPLACE INTO etf_names ({', '.join(cols)}) "
                        f"VALUES ({placeholders})",
                        values
                    )
                else:
                    cur.execute(
                        "INSERT OR REPLACE INTO etf_names (code, name) VALUES (?, ?)",
                        (code, name)
                    )
                conn.commit()
                return True
        except Exception as e:
            _logger.error(f"ETFRepository.upsert_name 失败: {e}")
            return False

    # ===== 内部辅助 =====

    def _build_list_codes_sql(self, role: PoolRole) -> Tuple[str, tuple]:
        """
        根据 role 构建 SQL

        US-001 阶段：etf_names 还没有 tradable/pool_role 字段，
        所以 list_codes 直接 SELECT code。
        US-002 之后会按 role 过滤：
            core:      tradable = 1 AND pool_role = 'core'
            reference: tradable = 0 AND pool_role = 'reference'
            excluded:  tradable = 0 AND pool_role = 'excluded'
        """
        cols = self._get_etf_names_columns()
        if 'tradable' in cols and 'pool_role' in cols:
            if role == 'core':
                return ("SELECT code FROM etf_names WHERE tradable = 1 AND pool_role = 'core' ORDER BY code", ())
            elif role == 'reference':
                return ("SELECT code FROM etf_names WHERE tradable = 0 AND pool_role = 'reference' ORDER BY code", ())
            elif role == 'excluded':
                return ("SELECT code FROM etf_names WHERE tradable = 0 AND pool_role = 'excluded' ORDER BY code", ())
        return ("SELECT code FROM etf_names ORDER BY code", ())

    def _build_list_with_meta_sql(self, role: PoolRole) -> Tuple[str, tuple]:
        cols = self._get_etf_names_columns()
        base = "SELECT code, name, exchange, aum FROM etf_names"
        if 'tradable' in cols and 'pool_role' in cols:
            if role == 'core':
                return (f"{base} WHERE tradable = 1 AND pool_role = 'core' ORDER BY code", ())
            elif role == 'reference':
                return (f"{base} WHERE tradable = 0 AND pool_role = 'reference' ORDER BY code", ())
            elif role == 'excluded':
                return (f"{base} WHERE tradable = 0 AND pool_role = 'excluded' ORDER BY code", ())
        return (f"{base} ORDER BY code", ())

    def _get_etf_names_columns(self) -> set:
        """读取 etf_names 表的字段集合（带缓存）"""
        if not hasattr(self, '_columns_cache'):
            try:
                with self._conn() as conn:
                    cur = conn.cursor()
                    cur.execute("PRAGMA table_info(etf_names)")
                    self._columns_cache = {row[1] for row in cur.fetchall()}
            except Exception as e:
                _logger.error(f"读取 etf_names 字段失败: {e}")
                self._columns_cache = set()
        return self._columns_cache
