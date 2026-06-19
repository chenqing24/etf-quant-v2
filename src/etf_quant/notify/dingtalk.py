"""
notify/dingtalk.py — 钉钉客户端（v2 notify 模块，US-016）

用途：钉钉 Webhook 客户端（text + markdown 消息）。
被谁调用：notify/notifier.py + notify/scenario.py。
按 v1 dingtalk_sender.py 适配。
"""
from __future__ import annotations

import os
import json
import logging
from typing import Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class DingTalkClient:
    """钉钉 Webhook 客户端（v2 notify）"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.environ.get("DINGTALK_WEBHOOK", "")

    def send_text(self, content: str, at_mobiles: list = None) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            logger.warning("DINGTALK_WEBHOOK 未配置，跳过推送")
            return False
        payload = {
            "msgtype": "text",
            "text": {"content": content},
        }
        if at_mobiles:
            payload["at"] = {"atMobiles": at_mobiles}
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError) as e:
            logger.error(f"钉钉推送失败: {e}")
            return False

    def send_markdown(self, title: str, content: str) -> bool:
        """发送 Markdown 消息"""
        if not self.webhook_url:
            logger.warning("DINGTALK_WEBHOOK 未配置，跳过推送")
            return False
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
        }
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError) as e:
            logger.error(f"钉钉推送失败: {e}")
            return False
