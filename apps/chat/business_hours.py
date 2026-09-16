"""Робочі години чату: Київ (Europe/Kyiv)."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

KYIV = ZoneInfo("Europe/Kyiv")

# weekday: Mon=0 … Sun=6 → (start, end) inclusive start, exclusive end
_SCHEDULE: dict[int, tuple[time, time] | None] = {
    0: (time(9, 0), time(18, 0)),   # Пн
    1: (time(9, 0), time(18, 0)),   # Вт
    2: (time(9, 0), time(18, 0)),   # Ср
    3: (time(9, 0), time(18, 0)),   # Чт
    4: (time(9, 0), time(18, 0)),   # Пт
    5: (time(10, 0), time(15, 0)),  # Сб
    6: None,                        # Нд — вихідний
}


def is_within_business_hours(when: datetime | None = None) -> bool:
    """True, якщо зараз (або when) у робочому графіку за Києвом."""
    dt = when or timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, KYIV)
    local = dt.astimezone(KYIV)
    window = _SCHEDULE.get(local.weekday())
    if window is None:
        return False
    start, end = window
    t = local.time()
    return start <= t < end
