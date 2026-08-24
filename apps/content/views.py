from django.shortcuts import get_object_or_404, render

from apps.content.models import Page
from apps.pricing.services import delivery_note, is_pro


def page(request, slug):
    page_obj = get_object_or_404(Page, slug=slug, is_active=True)
    user = request.user if request.user.is_authenticated else None
    context = {
        "page": page_obj,
        "show_pro_block": is_pro(user) and bool(page_obj.body_pro),
        "delivery_note": delivery_note(user),
    }
    return render(request, "content/page.html", context)
