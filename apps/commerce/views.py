import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.catalog.models import Variant
from apps.commerce import services
from apps.commerce.forms import CheckoutForm
from apps.commerce.models import Order
from apps.commerce.notifications import notify_new_order
from apps.commerce.services import CartError
from apps.loyalty import services as loyalty
from apps.payments.services import available_methods, build_liqpay_payload
from apps.pricing.services import delivery_note, free_delivery_threshold, min_order_amount


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _current_user(request):
    return request.user if request.user.is_authenticated else None


def _cart_payload(request):
    cart = services.get_cart(request, create=False)
    summary = services.cart_summary(cart, _current_user(request))
    return summary, {
        "count": summary["count"],
        "subtotal": str(summary["subtotal"]),
        "popup": render_to_string("commerce/_cart_popup.html", {"summary": summary}, request=request),
    }


def _cart_htmx_response(request, *, open_popup: bool = False):
    summary, payload = _cart_payload(request)
    response = render(
        request,
        "commerce/_cart_oob.html",
        {"summary": summary, "open_popup": open_popup},
    )
    trigger = {"cartUpdated": {"count": payload["count"]}}
    if open_popup:
        trigger["cartOpen"] = True
    response["HX-Trigger"] = json.dumps(trigger)
    return response


@require_POST
def cart_add(request):
    variant = get_object_or_404(Variant, pk=request.POST.get("variant_id"), is_active=True)
    cart = services.get_cart(request)
    try:
        services.add_item(cart, variant, request.POST.get("quantity", 1))
    except CartError as exc:
        if _is_htmx(request):
            return JsonResponse({"error": str(exc)}, status=400)
        messages.error(request, str(exc))
        return redirect(variant.product.get_absolute_url())

    if _is_htmx(request):
        return _cart_htmx_response(request, open_popup=True)

    _summary, payload = _cart_payload(request)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(payload)
    messages.success(request, _("Товар додано до кошика."))
    return redirect(variant.product.get_absolute_url())


@require_POST
def cart_update(request):
    cart = services.get_cart(request)
    services.set_quantity(cart, request.POST.get("item_id"), request.POST.get("quantity", 0))
    if _is_htmx(request):
        return _cart_htmx_response(request)
    _summary, payload = _cart_payload(request)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(payload)
    return redirect("commerce:cart")


@require_POST
def cart_remove(request):
    cart = services.get_cart(request)
    services.remove_item(cart, request.POST.get("item_id"))
    if _is_htmx(request):
        return _cart_htmx_response(request)
    _summary, payload = _cart_payload(request)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(payload)
    return redirect("commerce:cart")


def cart(request):
    user = _current_user(request)
    summary = services.cart_summary(services.get_cart(request, create=False), user)
    context = {
        "summary": summary,
        "delivery_note": delivery_note(user),
        "free_delivery_from": free_delivery_threshold(user),
        "min_order": min_order_amount(user),
    }
    return render(request, "commerce/cart.html", context)


def checkout(request):
    user = _current_user(request)
    cart_obj = services.get_cart(request, create=False)
    summary = services.cart_summary(cart_obj, user)
    if not summary["rows"]:
        messages.info(request, _("Кошик порожній."))
        return redirect("catalog:catalog")

    methods = available_methods()
    max_points = loyalty.max_redeemable_points(user, summary["subtotal"])
    initial = {}
    if user:
        initial = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email": user.email,
        }

    if request.method == "POST":
        form = CheckoutForm(request.POST, allowed_methods=methods, max_points=max_points)
        if form.is_valid():
            try:
                order = services.create_order(
                    request, cart_obj, form.cleaned_data, form.cleaned_data.get("redeem_points") or 0
                )
            except CartError as exc:
                messages.error(request, str(exc))
                return redirect("commerce:cart")
            notify_new_order(order)
            request.session["last_order"] = order.number
            return redirect("commerce:thanks", number=order.number)
    else:
        form = CheckoutForm(initial=initial, allowed_methods=methods, max_points=max_points)

    context = {
        "form": form,
        "summary": summary,
        "payment_methods": methods,
        "max_points": max_points,
        "points_value": loyalty.points_to_uah(max_points),
        "loyalty_balance": loyalty.get_balance(user) if user else 0,
        "delivery_note": delivery_note(user),
    }
    return render(request, "commerce/checkout.html", context)


def thanks(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    if request.session.get("last_order") != order.number and order.user != request.user:
        return redirect("core:home")
    context = {
        "order": order,
        "bank_details": order.bank_details_snapshot,
        "liqpay": build_liqpay_payload(order),
    }
    return render(request, "commerce/thanks.html", context)
