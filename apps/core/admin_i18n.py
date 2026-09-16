"""Допоміжні fieldsets для uk/ru-вкладок у django-unfold."""


def bilingual_fieldsets(common, uk_fields, ru_fields):
    """Спільні fieldsets + вкладки «Українська» / «Російська».

    ``common`` — список fieldsets без мовних полів.
    ``uk_fields`` / ``ru_fields`` — імена полів для відповідної вкладки.
    """
    return [
        *common,
        ("Українська", {"classes": ["tab"], "fields": list(uk_fields)}),
        ("Російська", {"classes": ["tab"], "fields": list(ru_fields)}),
    ]
