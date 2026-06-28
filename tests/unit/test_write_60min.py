"""
DataWriter.write_60min 单元测试（D-006 决策）
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import pytest
import pandas as pd
from etf_quant.data_layer.writer import DataWriter
from etf_quant.data_layer.exceptions import DataValidationError


@pytest.fixture
def writer(tmp_path):
    db_path = tmp_path / 'test_60min.db'
    w = DataWriter(db_path=str(db_path))
    yield w
    # cleanup 自动


def make_sample_df():
    return pd.DataFrame({
        'datetime': [
            '2026-06-23 10:30:00',
            '2026-06-23 11:30:00',
            '2026-06-23 14:00:00',
            '2026-06-23 15:00:00',
        ],
        'open': [1.0, 1.05, 1.08, 1.10],
        'high': [1.06, 1.10, 1.12, 1.15],
        'low':  [0.99, 1.04, 1.07, 1.09],
        'close':[1.05, 1.09, 1.11, 1.14],
        'volume': [10000, 20000, 30000, 40000],
    })


def test_write_60min_basic(writer):
    """基础写入测试"""
    df = make_sample_df()
    count = writer.write_60min('515050', df, source='akshare_60min')
    assert count == 4, f'应新增 4 条, 实际 {count}'


def test_write_60min_incremental(writer):
    """增量去重测试：再次写同一批数据，新增应为 0"""
    df = make_sample_df()
    writer.write_60min('515050', df, source='akshare_60min')
    count2 = writer.write_60min('515050', df, source='akshare_60min')
    assert count2 == 0, f'重复写入应新增 0 条, 实际 {count2}'


def test_write_60min_validation_high_low(writer):
    """业务约束：high < low 应拒绝"""
    df = make_sample_df()
    df.loc[0, 'high'] = 0.5  # 让 high < low
    with pytest.raises(DataValidationError):
        writer.write_60min('515050', df, source='akshare_60min')


def test_write_60min_validation_negative_price(writer):
    """业务约束：价格 <= 0 应拒绝"""
    df = make_sample_df()
    df.loc[0, 'close'] = 0
    with pytest.raises(DataValidationError):
        writer.write_60min('515050', df, source='akshare_60min')


def test_write_60min_missing_columns(writer):
    """缺列应拒绝"""
    df = make_sample_df().drop(columns=['volume'])
    with pytest.raises(DataValidationError):
        writer.write_60min('515050', df, source='akshare_60min')


def test_write_60min_batch(writer):
    """批量写入"""
    df = make_sample_df()
    results = writer.write_60min_batch({
        '515050': df,
        '512480': df.copy(),
    })
    assert results == {'515050': 4, '512480': 4}


def test_write_60min_table_indexes(writer):
    """索引检查（需先触发建表）"""
    import sqlite3
    df = make_sample_df()
    writer.write_60min('515050', df, source='akshare_60min')  # 触发建表
    conn = sqlite3.connect(writer.db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='etf_60min'")
    indexes = [r[0] for r in cur.fetchall()]
    conn.close()
    assert 'idx_60min_code' in indexes, '应有 idx_60min_code'
    assert 'idx_60min_dt' in indexes, '应有 idx_60min_dt'


def test_write_60min_unique_constraint(writer):
    """UNIQUE(code, datetime) 约束验证"""
    import sqlite3
    df = make_sample_df()
    writer.write_60min('515050', df, source='akshare_60min')
    conn = sqlite3.connect(writer.db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM etf_60min WHERE code='515050'")
    cnt = cur.fetchone()[0]
    conn.close()
    assert cnt == 4, f'UNIQUE 约束应保证 4 条不重复, 实际 {cnt}'