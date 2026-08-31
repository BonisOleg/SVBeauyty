from django.conf import settings
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


def _site_langs() -> frozenset[str]:
    return frozenset(code.split("-")[0] for code, _ in settings.LANGUAGES)


def localize_path(url: str, language: str | None = None) -> str:
    """Додає префікс поточної мови до внутрішнього шляху.

    Зберігає зовнішні URL (http/https/mailto/tel/#) без змін.
    Якщо в шляху вже є /uk/ або /ru/ — замінює на поточну мову.
    Очікуваний формат у CMS: ``/catalog/slug/`` без мовного префікса.
    """
    if not url:
        return ""
    path = str(url).strip()
    if not path:
        return ""
    lower = path.lower()
    if lower.startswith(("http://", "https://", "mailto:", "tel:", "//")) or path.startswith("#"):
        return path

    langs = _site_langs() or frozenset({"uk", "ru"})
    lang = (language or get_language() or settings.LANGUAGE_CODE or "uk").split("-")[0]
    if lang not in langs:
        lang = "uk"

    if not path.startswith("/"):
        path = f"/{path}"

    parts = path.split("/", 2)  # ['', 'uk', 'rest...'] or ['', 'catalog', ...]
    if len(parts) >= 2 and parts[1] in langs:
        rest = parts[2] if len(parts) > 2 else ""
        path = f"/{rest}" if rest else "/"

    if path == "/":
        return f"/{lang}/"
    return f"/{lang}{path}"
