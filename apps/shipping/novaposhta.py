"""Клієнт Нової Пошти з фолбеком на тестовий довідник."""

import json
import logging
from functools import lru_cache
from pathlib import Path

import requests
from django.conf import settings

from apps.shipping.models import ShippingSettings

logger = logging.getLogger(__name__)

API_URL = "https://api.novaposhta.ua/v2.0/json/"
TIMEOUT = 6
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "np_test_data.json"


@lru_cache(maxsize=1)
def _fixture() -> dict:
    if not FIXTURE.exists():
        return {"cities": [], "branches": {}}
    with FIXTURE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _api_key() -> str:
    """Ключ лише з .env. Адмінка його не зберігає (скіл: один відправник)."""
    if ShippingSettings.get_solo().use_test_data:
        return ""
    return (settings.NOVAPOSHTA_API_KEY or "").strip()


class NovaPoshtaError(Exception):
    pass


def api_call(model: str, method: str, props: dict, *, timeout: int = TIMEOUT) -> list:
    """Живий виклик. Порожній ключ і відхилення API — помилка, не тестовий довідник."""
    key = _api_key()
    if not key:
        raise NovaPoshtaError("Немає ключа Нової Пошти")
    payload = {
        "apiKey": key,
        "modelName": model,
        "calledMethod": method,
        "methodProperties": props,
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Nova Poshta API error: %s", exc)
        raise NovaPoshtaError("Нова Пошта не відповіла") from exc
    if not data.get("success"):
        logger.warning(
            "Nova Poshta API rejected model=%s method=%s response=%s",
            model,
            method,
            {k: v for k, v in data.items() if k != "data"},
        )
        errors = data.get("errors") or []
        raise NovaPoshtaError("; ".join(str(item) for item in errors) or "Нова Пошта відхилила запит")
    return data.get("data") or []


def _use_fixture() -> bool:
    from apps.shipping.models import NPCity

    conf = ShippingSettings.get_solo()
    if conf.use_test_data:
        return True
    return not NPCity.objects.filter(is_active=True).exists() and not _api_key()


def search_cities(query: str, limit: int = 20) -> list[dict]:
    needle = (query or "").strip().casefold()
    if len(needle) < 2:
        return []
    if _use_fixture():
        return _fixture_cities(needle, limit)
    return _rank_cities(needle, limit)


def get_branches(city_ref: str) -> list[dict]:
    if not city_ref:
        return []
    if _use_fixture():
        return list(_fixture()["branches"].get(city_ref, []))
    return _branches_from_db(city_ref)


def _fixture_cities(needle: str, limit: int) -> list[dict]:
    scored = []
    for city in _fixture()["cities"]:
        rank = _city_rank(city["name"], needle)
        if rank is None:
            continue
        scored.append((rank, city["name"], city))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]


def _rank_cities(needle: str, limit: int) -> list[dict]:
    from apps.shipping.models import NPCity

    scored = []
    for city in NPCity.objects.filter(is_active=True).only("ref", "name", "area"):
        rank = _city_rank(city.name, needle)
        if rank is None:
            continue
        scored.append((rank, city.name, {"ref": city.ref, "name": city.name, "area": city.area}))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]


def _city_rank(name: str, needle: str) -> int | None:
    folded = name.casefold()
    base = folded.split(" (", 1)[0]
    if folded == needle or base == needle:
        return 0
    if folded.startswith(needle) or base.startswith(needle):
        return 1
    if needle in base:
        return 3
    if needle in folded:
        return 4
    return None


def _branches_from_db(city_ref: str) -> list[dict]:
    from apps.shipping.models import NPWarehouse

    rows = []
    warehouses = NPWarehouse.objects.filter(city__ref=city_ref, is_active=True).exclude(category__iexact="Cargo")
    for warehouse in warehouses.only("ref", "description", "category", "number"):
        rows.append(
            {
                "ref": warehouse.ref,
                "name": warehouse.description,
                "category": warehouse.category,
                "number": warehouse.number,
            }
        )
    rows.sort(key=lambda row: (_warehouse_group(row["category"]), _number_key(row["number"]), row["name"]))
    return [{"ref": row["ref"], "name": row["name"]} for row in rows]


def _warehouse_group(category: str) -> int:
    return 1 if (category or "").casefold() == "postomat" else 0


def _number_key(number: str) -> tuple:
    digits = "".join(ch for ch in (number or "") if ch.isdigit())
    return (int(digits) if digits else 10**9, number or "")
