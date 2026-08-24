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
    conf = ShippingSettings.get_solo()
    if conf.use_test_data:
        return ""
    return conf.np_api_key or settings.NOVAPOSHTA_API_KEY


def _call(model: str, method: str, props: dict) -> list:
    key = _api_key()
    if not key:
        return []
    payload = {
        "apiKey": key,
        "modelName": model,
        "calledMethod": method,
        "methodProperties": props,
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Nova Poshta API error: %s", exc)
        return []
    if not data.get("success"):
        logger.warning("Nova Poshta API rejected: %s", data.get("errors"))
        return []
    return data.get("data", [])


def search_cities(query: str, limit: int = 20) -> list[dict]:
    query = (query or "").strip()
    if len(query) < 2:
        return []

    data = _call("Address", "searchSettlements", {"CityName": query, "Limit": str(limit)})
    if data:
        addresses = data[0].get("Addresses", [])
        return [
            {
                "ref": item.get("DeliveryCity") or item.get("Ref", ""),
                "name": item.get("MainDescription", ""),
                "area": item.get("Area", ""),
            }
            for item in addresses
            if item.get("DeliveryCity") or item.get("Ref")
        ]

    needle = query.lower()
    return [c for c in _fixture()["cities"] if needle in c["name"].lower()][:limit]


def get_branches(city_ref: str, limit: int = 100) -> list[dict]:
    if not city_ref:
        return []

    data = _call("Address", "getWarehouses", {"CityRef": city_ref, "Limit": str(limit)})
    if data:
        return [
            {"ref": item.get("Ref", ""), "name": item.get("Description", "")}
            for item in data
            if item.get("Ref")
        ]

    return _fixture()["branches"].get(city_ref, [])[:limit]
