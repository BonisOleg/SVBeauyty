from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from apps.accounts.forms import CosmetologistRequestForm, LoginForm, ProfileForm, RegisterForm
from apps.accounts.models import ClientType, CosmetologistRequest, RequestStatus
from apps.commerce.models import Order
from apps.loyalty import services as loyalty
from apps.pricing.services import delivery_note


class CabinetLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="apps.accounts.backends.EmailBackend")
            messages.success(request, _("Вітаємо! Обліковий запис створено."))
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Дані збережено."))
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    context = {
        "form": form,
        "loyalty_balance": loyalty.get_balance(request.user),
        "orders_count": Order.objects.filter(user=request.user).count(),
        "delivery_note": delivery_note(request.user),
        "pending_request": CosmetologistRequest.objects.filter(
            user=request.user, status=RequestStatus.NEW
        ).first(),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def orders(request):
    queryset = (
        Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
    )
    return render(request, "accounts/orders.html", {"orders": queryset})


@login_required
def order_detail(request, number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), number=number, user=request.user
    )
    return render(request, "accounts/order_detail.html", {"order": order, "bank_details": order.bank_details_snapshot})


@login_required
def loyalty_history(request):
    account = loyalty.get_account(request.user)
    transactions = account.transactions.select_related("order")[:100] if account else []
    context = {
        "balance": account.balance if account else 0,
        "transactions": transactions,
    }
    return render(request, "accounts/loyalty.html", context)


@login_required
def cosmetologist_request(request):
    if request.user.is_pro:
        messages.info(request, _("Статус косметолога вже активний."))
        return redirect("accounts:profile")

    existing = CosmetologistRequest.objects.filter(user=request.user, status=RequestStatus.NEW).first()
    if request.method == "POST" and not existing:
        form = CosmetologistRequestForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            request.user.client_type = ClientType.PENDING
            request.user.save(update_fields=["client_type"])
            messages.success(request, _("Заявку надіслано. Менеджер зв'яжеться з вами."))
            return redirect("accounts:profile")
    else:
        form = CosmetologistRequestForm(
            initial={"full_name": request.user.display_name, "phone": request.user.phone}
        )
    return render(request, "accounts/cosmetologist.html", {"form": form, "existing": existing})
