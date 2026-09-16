from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class CartStatus(models.TextChoices):
    ACTIVE = "active", _("Активний")
    CONVERTED = "converted", _("Оформлений")
    ABANDONED = "abandoned", _("Покинутий")


class Cart(TimeStampedModel):
    session_key = models.CharField(_("Сесія"), max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name=_("Клієнт"),
    )
    status = models.CharField(
        _("Статус"), max_length=16, choices=CartStatus.choices, default=CartStatus.ACTIVE
    )

    class Meta:
        verbose_name = _("Кошик")
        verbose_name_plural = _("Кошики")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Кошик #{self.pk}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("Кошик"))
    variant = models.ForeignKey(
        "catalog.Variant", on_delete=models.CASCADE, related_name="cart_items", verbose_name=_("Варіант")
    )
    quantity = models.PositiveIntegerField(_("Кількість"), default=1)

    class Meta:
        verbose_name = _("Позиція кошика")
        verbose_name_plural = _("Позиції кошика")
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="cart_unique_variant")]

    def __str__(self):
        return f"{self.variant} × {self.quantity}"


class OrderStatus(models.TextChoices):
    NEW = "new", _("Нове")
    PROCESSING = "processing", _("В обробці")
    AWAITING_PAYMENT = "awaiting_payment", _("Очікує оплати")
    PAID = "paid", _("Оплачено")
    SHIPPED = "shipped", _("Відправлено")
    DONE = "done", _("Виконано")
    CANCELED = "canceled", _("Скасовано")


class PaymentMethod(models.TextChoices):
    BANK_DETAILS = "bank_details", _("Переказ на рахунок ФОП")
    LIQPAY = "liqpay", _("Картка онлайн (LiqPay)")


class DeliveryMethod(models.TextChoices):
    NOVA_POSHTA = "nova_poshta", _("Нова Пошта")
    PICKUP = "pickup", _("Самовивіз")
    TAXI = "taxi", _("Таксі")


class Order(TimeStampedModel):
    number = models.CharField(_("Номер"), max_length=20, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Клієнт"),
    )
    client_type = models.CharField(_("Тип клієнта на момент покупки"), max_length=16, default="regular")

    first_name = models.CharField(_("Ім'я"), max_length=150)
    last_name = models.CharField(_("Прізвище"), max_length=150)
    phone = models.CharField(_("Телефон"), max_length=32)
    email = models.EmailField(_("Email"), blank=True)

    other_recipient = models.BooleanField(_("Інший отримувач"), default=False)
    recipient_first_name = models.CharField(_("Ім'я отримувача"), max_length=150, blank=True)
    recipient_last_name = models.CharField(_("Прізвище отримувача"), max_length=150, blank=True)
    recipient_phone = models.CharField(_("Телефон отримувача"), max_length=32, blank=True)

    delivery_method = models.CharField(
        _("Спосіб доставки"),
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.NOVA_POSHTA,
        db_index=True,
    )
    delivery_city = models.CharField(_("Місто"), max_length=160, blank=True)
    delivery_city_ref = models.CharField(_("Ref міста"), max_length=64, blank=True)
    delivery_branch = models.CharField(_("Відділення / адреса"), max_length=255, blank=True)
    delivery_branch_ref = models.CharField(_("Ref відділення"), max_length=64, blank=True)
    delivery_address = models.CharField(
        _("Адреса (таксі)"),
        max_length=255,
        blank=True,
        help_text=_("Вулиця, будинок, квартира для доставки таксі."),
    )

    payment_method = models.CharField(
        _("Оплата"), max_length=16, choices=PaymentMethod.choices, default=PaymentMethod.BANK_DETAILS
    )
    status = models.CharField(
        _("Статус"), max_length=20, choices=OrderStatus.choices, default=OrderStatus.NEW, db_index=True
    )

    subtotal_uah = models.DecimalField(_("Сума позицій"), max_digits=10, decimal_places=2, default=0)
    loyalty_spent_points = models.PositiveIntegerField(_("Списано балів"), default=0)
    loyalty_discount_uah = models.DecimalField(
        _("Знижка балами, грн"), max_digits=10, decimal_places=2, default=0
    )
    total_uah = models.DecimalField(_("До сплати"), max_digits=10, decimal_places=2, default=0)

    bank_details_snapshot = models.JSONField(_("Реквізити"), default=dict, blank=True)
    comment = models.TextField(_("Коментар клієнта"), blank=True)
    gdpr_accepted = models.BooleanField(_("Згода на обробку даних"), default=False)
    locale = models.CharField(_("Мова"), max_length=2, default="uk")

    class Meta:
        verbose_name = _("Замовлення")
        verbose_name_plural = _("Замовлення")
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @property
    def customer_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def recipient_name(self) -> str:
        if not self.other_recipient:
            return self.customer_name
        return f"{self.recipient_first_name} {self.recipient_last_name}".strip() or self.customer_name

    @property
    def delivery_phone(self) -> str:
        if self.other_recipient and self.recipient_phone:
            return self.recipient_phone
        return self.phone

    @property
    def delivery_summary(self) -> str:
        method = self.get_delivery_method_display()
        if self.delivery_method == DeliveryMethod.NOVA_POSHTA:
            parts = [method, self.delivery_city, self.delivery_branch]
        else:
            parts = [method, self.delivery_address or self.delivery_branch]
        return ", ".join(part for part in parts if part)

    @property
    def is_paid(self) -> bool:
        return self.status in {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DONE}

    def recalculate(self):
        self.subtotal_uah = sum((i.line_total_uah for i in self.items.all()), Decimal("0.00"))
        self.total_uah = max(Decimal("0.00"), self.subtotal_uah - Decimal(self.loyalty_discount_uah))


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("Замовлення"))
    variant = models.ForeignKey(
        "catalog.Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("Варіант"),
    )
    product_name = models.CharField(_("Товар"), max_length=255)
    sku = models.CharField(_("Артикул"), max_length=64)
    volume = models.CharField(_("Об'єм"), max_length=32, blank=True)
    unit_price_uah = models.DecimalField(_("Ціна за одиницю"), max_digits=10, decimal_places=2)
    unit_purchase_price_uah = models.DecimalField(
        _("Закупівельна за одиницю"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_source = models.CharField(_("Джерело ціни"), max_length=16, default="retail")
    quantity = models.PositiveIntegerField(_("Кількість"), default=1)
    line_total_uah = models.DecimalField(_("Сума"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Позиція замовлення")
        verbose_name_plural = _("Позиції замовлення")

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    def save(self, *args, **kwargs):
        self.line_total_uah = Decimal(self.unit_price_uah) * self.quantity
        super().save(*args, **kwargs)

    @property
    def margin_uah(self):
        if self.unit_purchase_price_uah is None:
            return None
        return (Decimal(self.unit_price_uah) - Decimal(self.unit_purchase_price_uah)) * self.quantity


class OrderStatusLog(TimeStampedModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_logs", verbose_name=_("Замовлення")
    )
    old_status = models.CharField(_("Було"), max_length=20, blank=True)
    new_status = models.CharField(_("Стало"), max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Хто змінив"),
    )

    class Meta:
        verbose_name = _("Історія статусу")
        verbose_name_plural = _("Історія статусів")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.number}: {self.old_status} → {self.new_status}"
