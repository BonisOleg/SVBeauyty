from django import template

from apps.catalog.product_grid import pick_grid_columns as _pick_grid_columns

register = template.Library()


@register.filter
def pick_grid_columns(count):
    try:
        return _pick_grid_columns(int(count))
    except (TypeError, ValueError):
        return 2


@register.inclusion_tag("catalog/_product_grid.html", takes_context=True)
def product_grid(context, products=None, cols=None):
    """Сітка карток з flex-центруванням неповного останнього ряду.

    cols: якщо задано (напр. 4 для пагінованого каталогу) — фіксовані колонки;
    інакше — pick_grid_columns(len(products)).
    """
    items = list(products) if products is not None else []
    if cols is None:
        grid_cols = _pick_grid_columns(len(items))
    else:
        try:
            grid_cols = int(cols)
        except (TypeError, ValueError):
            grid_cols = _pick_grid_columns(len(items))
    return {
        "request": context.get("request"),
        "products": items,
        "grid_cols": grid_cols,
    }
