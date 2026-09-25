"""Синк довідника Нової Пошти. Page і Limit — рядки, інакше API віддає 0 рядків."""

from apps.shipping.models import NPCity, NPWarehouse
from apps.shipping.novaposhta import api_call

PAGE_LIMIT = "500"
MAX_PAGES = 400


def sync_directory() -> dict:
    cities = list(_pages("Address", "getCities"))
    _save_cities(cities)
    city_ids = dict(NPCity.objects.values_list("ref", "id"))
    warehouses = list(_pages("Address", "getWarehouses"))
    saved = _save_warehouses(warehouses, city_ids)
    return {"cities": len(cities), "warehouses": saved}


def _pages(model: str, method: str):
    seen = set()
    page = 1
    while page <= MAX_PAGES:
        rows = api_call(
            model,
            method,
            {"Page": str(page), "Limit": PAGE_LIMIT},
            timeout=30,
        )
        if not rows:
            break
        fresh = 0
        for row in rows:
            ref = row.get("Ref") or ""
            if not ref or ref in seen:
                continue
            seen.add(ref)
            fresh += 1
            yield row
        if fresh == 0 or len(rows) < int(PAGE_LIMIT):
            break
        page += 1


def _save_cities(rows: list[dict]) -> None:
    refs = []
    batch = []
    for row in rows:
        ref = row.get("Ref") or ""
        name = (row.get("Description") or "").strip()
        if not ref or not name:
            continue
        refs.append(ref)
        batch.append(
            NPCity(
                ref=ref,
                name=name[:255],
                area=(row.get("AreaDescription") or "")[:255],
                is_active=True,
            )
        )
        if len(batch) >= 500:
            _upsert_cities(batch)
            batch = []
    if batch:
        _upsert_cities(batch)
    if refs:
        NPCity.objects.exclude(ref__in=refs).update(is_active=False)


def _upsert_cities(batch: list[NPCity]) -> None:
    NPCity.objects.bulk_create(
        batch,
        update_conflicts=True,
        unique_fields=["ref"],
        update_fields=["name", "area", "is_active"],
    )


def _save_warehouses(rows: list[dict], city_ids: dict[str, int]) -> int:
    refs = []
    batch = []
    for row in rows:
        ref = row.get("Ref") or ""
        city_id = city_ids.get(row.get("CityRef") or "")
        description = (row.get("Description") or "").strip()
        if not ref or not city_id or not description:
            continue
        refs.append(ref)
        batch.append(
            NPWarehouse(
                ref=ref,
                city_id=city_id,
                number=(row.get("Number") or "")[:16],
                description=description[:512],
                category=(row.get("CategoryOfWarehouse") or "")[:32],
                is_active=True,
            )
        )
        if len(batch) >= 500:
            _upsert_warehouses(batch)
            batch = []
    if batch:
        _upsert_warehouses(batch)
    if refs:
        NPWarehouse.objects.exclude(ref__in=refs).update(is_active=False)
    return len(refs)


def _upsert_warehouses(batch: list[NPWarehouse]) -> None:
    NPWarehouse.objects.bulk_create(
        batch,
        update_conflicts=True,
        unique_fields=["ref"],
        update_fields=["city", "number", "description", "category", "is_active"],
    )
