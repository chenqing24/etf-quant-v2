"""
monitor/business_alert.py — 业务告警监控（v2 monitor 模块）

业务层告警：
- 持仓超过止盈止损阈值
- 因子 IC 衰减（批量计算后）
- 策略连续亏损天数
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from etf_quant.data_layer.loader import DataLoader
from etf_quant.config.constants import DATA_DIR, DB_NAME
from etf_quant.universe import ETFListLoader


@dataclass
class BusinessAlert:
    """业务告警"""
    severity: str  # INFO / WARN / CRITICAL
    code: str
    message: str


class BusinessAlertMonitor:
    """业务告警监控器"""

    def __init__(self, loader: DataLoader = None):
        if loader is None:
            db_path = f"{DATA_DIR}/{DB_NAME}"
            loader = DataLoader(db_path=db_path)
        self.loader = loader

    def check_stop_loss(self, threshold_pct: float = -5.0) -> List[BusinessAlert]:
        """检查止损告警"""
        alerts = []
        # 简化：从 trade_history 查最近持仓
        try:
            positions = self.loader._conn().execute(
                "SELECT code, price FROM trade_history ORDER BY date DESC LIMIT 10"
            ).fetchall()
        except Exception:
            positions = []
        for pos in positions:
            # 简化：未计算 PnL（需配合 execution tracker）
            alerts.append(BusinessAlert(
                severity="INFO",
                code=pos[0] if isinstance(pos, tuple) else pos.get("code", ""),
                message=f"持仓 {pos[0] if isinstance(pos, tuple) else pos.get('code', '')}",
            ))
        return alerts
