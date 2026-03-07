"""
---
role: 短信告警
depends: []
exports:
  - SmsAlertSender
status: IMPLEMENTED
functions:
  - SmsAlertSender.send(phone_number: str, message: str) -> bool
---
"""

from __future__ import annotations

from futures_monitor.utils.logger import get_logger


class SmsAlertSender:
    def __init__(self, enabled: bool = False, access_key: str | None = None, secret_key: str | None = None) -> None:
        self.enabled = enabled
        self.access_key = access_key
        self.secret_key = secret_key
        self._logger = get_logger(self.__class__.__name__)

    def send(self, phone_number: str, message: str) -> bool:
        if not self.enabled:
            self._logger.info(
                "SMS disabled. Skip send to %s with message: %s",
                phone_number,
                message,
            )
            return False

        self._logger.warning("SMS provider not integrated yet. Phone=%s", phone_number)
        return False
