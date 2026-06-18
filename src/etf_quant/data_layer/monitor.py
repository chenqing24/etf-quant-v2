#!/usr/bin/env python3
"""
数据质量监控模块

功能：
- 检查数据新鲜度
- 检查数据完整性
- 检查存储健康度
- 生成监控报告

使用方式：
    # 检查并输出报告
    python -m src.data.monitor
    
    # 检查并输出JSON
    python -m src.data.monitor --json
    
    # 发送到钉钉
    python -m src.data.monitor --dingtalk
"""
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etf_quant.config.constants import DATA_DIR, DB_NAME


# 工作日判断（A股周一至周五）
WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def is_trading_day(dt: datetime = None) -> bool:
    """
    判断是否为A股交易日（周一至周五）
    
    注意：节假日需要外部补充，这里只做基础判断
    """
    if dt is None:
        dt = datetime.now()
    return dt.weekday() < 5  # 0-4 是周一到周五


class DataQualityMonitor:
    """数据质量监控器"""
    
    # 告警阈值（分钟级）
    THRESHOLDS = {
        'max_delay_minutes': 80,       # 数据延迟超过80分钟告警
        'min_active_etfs': 30,        # 活跃ETF少于30个告警
        'max_missing_pct': 0.15,      # 缺失超过15%告警
        'max_db_size_mb': 100,        # 数据库超过100MB提示
        # 交易日完整性检查
        'max_day_missing_pct': 0.20,  # 交易日数据缺失超过20%告警
        'min_day_count': 50,          # 交易日数据最少50条才正常
    }
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(DATA_DIR, DB_NAME)
        self.alerts: List[Dict] = []  # ERROR级别
        self.warnings: List[Dict] = []  # WARNING级别
        self.report: Dict[str, Any] = {}
    
    def check_all(self) -> Dict[str, Any]:
        """执行所有检查"""
        self.alerts = []  # ERROR级别
        self.warnings = []  # WARNING级别
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'freshness': self.check_data_freshness(),
            'completeness': self.check_data_completeness(),
            'storage': self.check_storage_health(),
            'alerts': self.alerts,    # ERROR only
            'warnings': self.warnings  # WARNING only
        }
        
        self.report = report
        return report
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """检查数据新鲜度（分钟级）
        
        逻辑：
        1. 获取上一个交易日（周末往前推）
        2. 检查是否有所需的交易日数据
        3. 如果有，计算入库时间与当前时间的延迟分钟数
        4. 超过阈值告警
        """
        if not Path(self.db_path).exists():
            return {
                'status': 'ERROR',
                'message': '数据库文件不存在',
                'latest_date': None,
                'delay_minutes': None
            }
        
        try:
            now = datetime.now()
            is_trade_day = is_trading_day(now)
            
            # 计算上一个交易日
            weekday = now.weekday()
            if weekday == 0:  # 周一
                last_trading_day = (now - timedelta(days=3)).strftime('%Y-%m-%d')
            elif weekday == 6:  # 周日
                last_trading_day = (now - timedelta(days=2)).strftime('%Y-%m-%d')
            else:
                last_trading_day = (now - timedelta(days=1)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            
            # 获取最新日期和对应的入库时间
            cur = conn.execute('''
                SELECT date, MAX(updated_at) as last_update
                FROM daily
                GROUP BY date
                ORDER BY date DESC
                LIMIT 1
            ''')
            row = cur.fetchone()
            
            # 获取上一交易日的记录数
            cur2 = conn.execute(
                'SELECT COUNT(*) FROM daily WHERE date = ?',
                (last_trading_day,)
            )
            last_trading_day_count = cur2.fetchone()[0]
            
            conn.close()
            
            if row is None or row[0] is None:
                return {
                    'status': 'ERROR',
                    'message': '无数据',
                    'latest_date': None,
                    'delay_minutes': None
                }
            
            latest_date = row[0]
            last_update_str = row[1]
            
            # 计算延迟分钟数
            if last_update_str:
                try:
                    last_update = datetime.fromisoformat(last_update_str)
                    delay_minutes = (now - last_update).total_seconds() / 60
                except:
                    delay_minutes = None
            else:
                delay_minutes = None
            
            # 判断状态
            if not is_trade_day:
                # 非交易日（周末）：OK，不需要告警
                return {
                    'status': 'OK',
                    'message': '非交易日，数据正常',
                    'latest_date': latest_date,
                    'last_update': last_update_str,
                    'delay_minutes': delay_minutes,
                    'is_trading_day': False,
                    'last_trading_day': last_trading_day,
                    'last_trading_day_count': last_trading_day_count
                }
            
            # 工作日 09:00 检查：必须有上一个交易日的数据
            if latest_date < last_trading_day:
                # 数据缺失：期望last_trading_day，但实际最新是latest_date
                status = 'ERROR'
                self.alerts.append({
                    'type': 'freshness',
                    'level': 'ERROR',
                    'message': f'数据缺失: 期望{last_trading_day}，实际{latest_date}',
                    'detail': f"延迟{(now - datetime.strptime(latest_date, '%Y-%m-%d')).days}天"
                })
            elif delay_minutes is not None and delay_minutes > self.THRESHOLDS['max_delay_minutes']:
                # 数据延迟超过80分钟
                status = 'WARNING'
                self.warnings.append({
                    'type': 'freshness',
                    'level': 'WARNING',
                    'message': f'数据延迟 {delay_minutes:.0f} 分钟（阈值{self.THRESHOLDS["max_delay_minutes"]}分钟）',
                    'detail': f'最新入库: {last_update_str}'
                })
            else:
                # 数据正常
                status = 'OK'
            
            return {
                'status': status,
                'latest_date': latest_date,
                'last_update': last_update_str,
                'delay_minutes': delay_minutes,
                'is_trading_day': True,
                'last_trading_day': last_trading_day,
                'last_trading_day_count': last_trading_day_count
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': str(e),
                'latest_date': None,
                'delay_minutes': None
            }
    
    def check_data_completeness(self) -> Dict[str, Any]:
        """检查数据完整性
        
        包含两部分：
        1. 历史完整性：ETF数量和历史数据行数
        2. 交易日完整性：上一交易日的数据条数是否正常
        """
        if not Path(self.db_path).exists():
            return {'status': 'ERROR', 'message': '数据库文件不存在'}
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # === 1. 历史完整性检查 ===
            cur = conn.execute('SELECT COUNT(DISTINCT code) FROM daily')
            total_etfs = cur.fetchone()[0]
            
            cur = conn.execute('''
                SELECT code, COUNT(*) as cnt 
                FROM daily 
                GROUP BY code 
                ORDER BY cnt DESC
            ''')
            etf_counts = {row[0]: row[1] for row in cur.fetchall()}
            
            try:
                from src.config.etf_pools import ETF_POOLS
                expected_etfs = len(ETF_POOLS.get('core', [])) + len(ETF_POOLS.get('extended', []))
            except:
                expected_etfs = total_etfs
            
            missing_count = max(0, expected_etfs - len(etf_counts))
            missing_pct = missing_count / expected_etfs if expected_etfs > 0 else 0
            
            # === 2. 交易日完整性检查 ===
            now = datetime.now()
            is_trade_day = is_trading_day(now)
            
            # 计算上一交易日
            weekday = now.weekday()
            if weekday == 0:  # 周一
                last_trading_day = (now - timedelta(days=3)).strftime('%Y-%m-%d')
            elif weekday == 6:  # 周日
                last_trading_day = (now - timedelta(days=2)).strftime('%Y-%m-%d')
            else:
                last_trading_day = (now - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # 获取上一交易日记录数
            cur = conn.execute(
                'SELECT COUNT(*) FROM daily WHERE date = ?',
                (last_trading_day,)
            )
            last_day_count = cur.fetchone()[0]
            
            # 获取前一个交易日记录数（基准）
            prev_day = (datetime.strptime(last_trading_day, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            cur = conn.execute(
                'SELECT COUNT(*) FROM daily WHERE date = ?',
                (prev_day,)
            )
            prev_day_count = cur.fetchone()[0]
            
            conn.close()
            
            # === 判断状态 ===
            # 初始化状态
            status = 'OK'
            trade_day_status = 'OK'
            
            # 1. 历史完整性
            if missing_pct > self.THRESHOLDS['max_missing_pct']:
                status = 'ERROR'
                self.alerts.append({
                    'type': 'completeness',
                    'level': 'ERROR',
                    'message': f'缺失 {missing_count} 只ETF ({missing_pct:.1%})',
                    'detail': f'配置 {expected_etfs} 只, 实际 {total_etfs} 只'
                })
            elif missing_count > 0:
                if status != 'ERROR':
                    status = 'WARNING'
                self.warnings.append({
                    'type': 'completeness',
                    'level': 'WARNING',
                    'message': f'缺失 {missing_count} 只ETF ({missing_pct:.1%})',
                    'detail': f'配置 {expected_etfs} 只, 实际 {total_etfs} 只'
                })
            
            # 2. 交易日完整性（仅交易时段检查）
            if is_trade_day:
                # 基准：前一个交易日的记录数
                baseline_count = prev_day_count if prev_day_count > 0 else 60  # 默认60条
                
                if last_day_count == 0:
                    # 没有数据
                    trade_day_status = 'ERROR'
                    self.alerts.append({
                        'type': 'trade_day_completeness',
                        'level': 'ERROR',
                        'message': f'交易日 {last_trading_day} 无数据',
                        'detail': f'基准: {baseline_count}条'
                    })
                elif last_day_count < self.THRESHOLDS['min_day_count']:
                    # 数据太少
                    trade_day_status = 'ERROR'
                    self.alerts.append({
                        'type': 'trade_day_completeness',
                        'level': 'ERROR',
                        'message': f'交易日 {last_trading_day} 数据不足 ({last_day_count}条)',
                        'detail': f'基准: {baseline_count}条, 阈值: {self.THRESHOLDS["min_day_count"]}条'
                    })
                elif last_day_count < baseline_count * (1 - self.THRESHOLDS['max_day_missing_pct']):
                    # 数据缺失超过阈值
                    day_missing_pct = (baseline_count - last_day_count) / baseline_count
                    trade_day_status = 'WARNING'
                    self.warnings.append({
                        'type': 'trade_day_completeness',
                        'level': 'WARNING',
                        'message': f'交易日 {last_trading_day} 数据缺失 {day_missing_pct:.1%}',
                        'detail': f'实际: {last_day_count}条, 基准: {baseline_count}条'
                    })
                
                if trade_day_status == 'ERROR':
                    status = 'ERROR'
                elif trade_day_status == 'WARNING' and status != 'ERROR':
                    status = 'WARNING'
            
            # 找出数据不足的ETF（少于100行）
            insufficient = [code for code, cnt in etf_counts.items() if cnt < 100]
            
            return {
                'status': status,
                'total_etfs': total_etfs,
                'expected_etfs': expected_etfs,
                'missing_count': missing_count,
                'missing_pct': round(missing_pct * 100, 1),
                'avg_rows': round(sum(etf_counts.values()) / len(etf_counts), 0) if etf_counts else 0,
                'insufficient_etfs': len(insufficient),
                'top_etfs': list(etf_counts.items())[:5],
                # 交易日完整性
                'last_trading_day': last_trading_day,
                'last_day_count': last_day_count,
                'prev_day_count': prev_day_count,
                'is_trading_day': is_trade_day,
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}
    
    def check_storage_health(self) -> Dict[str, Any]:
        """检查存储健康度"""
        if not Path(self.db_path).exists():
            return {'status': 'ERROR', 'message': '数据库文件不存在'}
        
        try:
            stat = Path(self.db_path).stat()
            db_size_mb = stat.st_size / 1024 / 1024
            
            conn = sqlite3.connect(self.db_path)
            
            # 获取总记录数
            cur = conn.execute('SELECT COUNT(*) FROM daily')
            total_records = cur.fetchone()[0]
            
            # 获取各表记录数
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            
            table_stats = {}
            for table in tables:
                try:
                    cur = conn.execute(f'SELECT COUNT(*) FROM {table}')
                    table_stats[table] = cur.fetchone()[0]
                except:
                    table_stats[table] = 0
            
            # 检查索引
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cur.fetchall()]
            
            conn.close()
            
            # 判断状态
            if db_size_mb > self.THRESHOLDS['max_db_size_mb']:
                status = 'WARNING'
                self.warnings.append({
                    'type': 'storage',
                    'level': 'WARNING',
                    'message': f'数据库较大 ({db_size_mb:.1f} MB)',
                    'detail': '建议执行 VACUUM 优化'
                })
            else:
                status = 'OK'
            
            return {
                'status': status,
                'db_size_mb': round(db_size_mb, 2),
                'total_records': total_records,
                'tables': table_stats,
                'indexes': len(indexes),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}
    
    def format_report(self) -> str:
        """格式化报告为可读字符串"""
        if not self.report:
            self.check_all()
        
        r = self.report
        alerts = r.get('alerts', [])
        warnings = r.get('warnings', [])
        freshness = r.get('freshness', {})
        
        # 计算显示的延迟信息
        delay_info = ""
        if freshness.get('delay_minutes') is not None:
            mins = freshness['delay_minutes']
            if mins >= 60:
                delay_info = f"{mins/60:.1f} 小时"
            else:
                delay_info = f"{mins:.0f} 分钟"
        elif freshness.get('delay_days') is not None:
            delay_info = f"{freshness['delay_days']} 天"
        
        lines = [
            "=" * 50,
            "📊 数据质量监控报告",
            "=" * 50,
            f"时间: {r['timestamp']}",
            f"类型: {'📈 交易日' if freshness.get('is_trading_day', False) else '📅 非交易日'}",
            "",
            "【新鲜度】",
            f"  状态: {freshness.get('status', 'N/A')}",
            f"  最新日期: {freshness.get('latest_date', 'N/A')}",
            f"  延迟: {delay_info if delay_info else 'N/A'}",
            f"  入库时间: {freshness.get('last_update', 'N/A')}",
            "",
            "【完整性】",
            f"  状态: {r['completeness'].get('status', 'N/A')}",
            f"  ETF数量: {r['completeness'].get('total_etfs', 0)}/{r['completeness'].get('expected_etfs', 0)}",
            f"  缺失: {r['completeness'].get('missing_count', 0)} 只",
            f"  交易日: {r['completeness'].get('last_trading_day', 'N/A')} ({r['completeness'].get('last_day_count', 0)}条)",
            f"  基准: {r['completeness'].get('prev_day_count', 0)}条",
            "",
            "【存储】",
            f"  状态: {r['storage'].get('status', 'N/A')}",
            f"  数据库大小: {r['storage'].get('db_size_mb', 0)} MB",
            f"  总记录数: {r['storage'].get('total_records', 0)}",
            "",
        ]
        
        if alerts:
            lines.append("【告警】")
            for a in alerts:
                lines.append(f"  🔴 {a['message']}")
                if a.get('detail'):
                    lines.append(f"      {a['detail']}")
        else:
            lines.append("【告警】无")
        
        if warnings:
            lines.append("")
            lines.append("【警告】")
            for w in warnings:
                lines.append(f"  ⚠️ {w['message']}")
                if w.get('detail'):
                    lines.append(f"      {w['detail']}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='数据质量监控')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    parser.add_argument('--dingtalk', action='store_true', help='发送到钉钉')
    parser.add_argument('--db-path', type=str, help='数据库路径')
    
    args = parser.parse_args()
    
    monitor = DataQualityMonitor(db_path=args.db_path)
    report = monitor.check_all()
    
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(monitor.format_report())
    
    # 告警或警告时发送到钉钉
    if args.dingtalk and (report.get('alerts') or report.get('warnings')):
        try:
            from src.notify.dingtalk import DingTalkSender
            sender = DingTalkSender(mode='qwenpaw')
            message = monitor.format_report()
            sender.send(message)
            print("\n📨 已发送钉钉通知")
        except Exception as e:
            print(f"\n⚠️ 钉钉发送失败: {e}")


if __name__ == '__main__':
    main()