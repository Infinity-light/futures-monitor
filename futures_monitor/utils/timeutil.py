"""
---
role: 时间工具
depends: []
exports:
  - now_local
  - is_after_1445
  - is_after_1455
status: IMPLEMENTED
functions:
  - now_local() -> datetime
  - is_after_1445(dt: datetime) -> bool
  - is_after_1455(dt: datetime) -> bool
---
"""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

_DEFAULT_TZ = "Asia/Shanghai"


def now_local() -> datetime:
    return datetime.now(ZoneInfo(_DEFAULT_TZ))


def is_after_1445(dt: datetime) -> bool:
    return dt.time() >= time(14, 45)


def is_after_1455(dt: datetime) -> bool:
    return dt.time() >= time(14, 55)
