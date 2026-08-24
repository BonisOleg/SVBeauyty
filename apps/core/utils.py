from django.utils.translation import get_language


def localized(obj, field: str, language: str | None = None):
    """Повертає значення поля мовою інтерфейсу з фолбеком на українську."""
    lang = (language or get_language() or "uk").split("-")[0]
    if lang not in {"uk", "ru"}:
        lang = "uk"
    value = getattr(obj, f"{field}_{lang}", "") or ""
    if not value and lang != "uk":
        value = getattr(obj, f"{field}_uk", "") or ""
    return value
