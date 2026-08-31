from django import forms
from django.utils.translation import gettext_lazy as _

from apps.commerce.models import DeliveryMethod, PaymentMethod
from apps.shipping.models import ShippingSettings


class CheckoutForm(forms.Form):
    first_name = forms.CharField(label=_("Ім'я"), max_length=150)
    last_name = forms.CharField(label=_("Прізвище"), max_length=150)
    phone = forms.CharField(label=_("Телефон"), max_length=32)
    email = forms.EmailField(label=_("Email"), required=False)

    other_recipient = forms.BooleanField(
        label=_("Отримувач інша людина"),
        required=False,
        help_text=_("Увімкніть, якщо замовлення забере або отримає не замовник."),
    )
    recipient_first_name = forms.CharField(label=_("Ім'я отримувача"), max_length=150, required=False)
    recipient_last_name = forms.CharField(label=_("Прізвище отримувача"), max_length=150, required=False)
    recipient_phone = forms.CharField(label=_("Телефон отримувача"), max_length=32, required=False)

    delivery_method = forms.ChoiceField(
        label=_("Спосіб доставки"),
        choices=DeliveryMethod.choices,
        initial=DeliveryMethod.NOVA_POSHTA,
        widget=forms.RadioSelect,
    )
    delivery_city = forms.CharField(label=_("Місто"), max_length=160, required=False)
    delivery_city_ref = forms.CharField(max_length=64, required=False, widget=forms.HiddenInput())
    delivery_branch = forms.CharField(
        label=_("Відділення Нової Пошти"), max_length=255, required=False
    )
    delivery_branch_ref = forms.CharField(max_length=64, required=False, widget=forms.HiddenInput())
    delivery_address = forms.CharField(
        label=_("Адреса доставки"),
        max_length=255,
        required=False,
        help_text=_("Для таксі: вулиця, будинок, квартира."),
    )

    payment_method = forms.ChoiceField(label=_("Спосіб оплати"), choices=PaymentMethod.choices)
    comment = forms.CharField(
        label=_("Коментар"), required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    redeem_points = forms.IntegerField(label=_("Списати балів"), required=False, min_value=0)
    gdpr_accepted = forms.BooleanField(label=_("Погоджуюсь на обробку персональних даних"))

    def __init__(self, *args, allowed_methods=None, max_points=0, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_methods:
            self.fields["payment_method"].choices = [(m.code, m.label) for m in allowed_methods]
        self.max_points = max_points
        self.shipping = ShippingSettings.get_solo()
        self.fields["delivery_method"].choices = self._delivery_choices()
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["email"].widget.attrs.update({"inputmode": "email", "autocomplete": "email"})
        self.fields["recipient_phone"].widget.attrs.update(
            {"inputmode": "tel", "autocomplete": "tel"}
        )

    def _delivery_choices(self):
        choices = [(DeliveryMethod.NOVA_POSHTA, DeliveryMethod.NOVA_POSHTA.label)]
        if self.shipping.pickup_enabled:
            choices.append((DeliveryMethod.PICKUP, DeliveryMethod.PICKUP.label))
        if self.shipping.taxi_enabled:
            choices.append((DeliveryMethod.TAXI, DeliveryMethod.TAXI.label))
        return choices

    def clean_phone(self):
        phone = "".join(ch for ch in self.cleaned_data["phone"] if ch.isdigit() or ch == "+")
        if len(phone.lstrip("+")) < 9:
            raise forms.ValidationError(_("Вкажіть коректний номер телефону."))
        return phone

    def clean_recipient_phone(self):
        raw = self.cleaned_data.get("recipient_phone") or ""
        phone = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        return phone

    def clean_redeem_points(self):
        points = self.cleaned_data.get("redeem_points") or 0
        if points > self.max_points:
            raise forms.ValidationError(_("Доступно максимум %(n)s балів.") % {"n": self.max_points})
        return points

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("delivery_method") or DeliveryMethod.NOVA_POSHTA
        shipping = self.shipping

        if cleaned.get("other_recipient"):
            if not (cleaned.get("recipient_first_name") or "").strip():
                self.add_error("recipient_first_name", _("Вкажіть імʼя отримувача."))
            if not (cleaned.get("recipient_last_name") or "").strip():
                self.add_error("recipient_last_name", _("Вкажіть прізвище отримувача."))
            recipient_phone = cleaned.get("recipient_phone") or ""
            if len(recipient_phone.lstrip("+")) < 9:
                self.add_error("recipient_phone", _("Вкажіть коректний телефон отримувача."))
        else:
            cleaned["recipient_first_name"] = ""
            cleaned["recipient_last_name"] = ""
            cleaned["recipient_phone"] = ""

        if method == DeliveryMethod.NOVA_POSHTA:
            city = (cleaned.get("delivery_city") or "").strip()
            city_ref = (cleaned.get("delivery_city_ref") or "").strip()
            branch = (cleaned.get("delivery_branch") or "").strip()
            branch_ref = (cleaned.get("delivery_branch_ref") or "").strip()
            if not city:
                self.add_error("delivery_city", _("Вкажіть місто."))
            elif not city_ref:
                self.add_error("delivery_city", _("Оберіть місто зі списку."))
            if not branch:
                self.add_error("delivery_branch", _("Вкажіть відділення Нової Пошти."))
            elif not branch_ref:
                self.add_error("delivery_branch", _("Оберіть відділення зі списку."))
            cleaned["delivery_address"] = ""
        elif method == DeliveryMethod.PICKUP:
            if not shipping.pickup_enabled:
                self.add_error("delivery_method", _("Самовивіз тимчасово недоступний."))
            address = (shipping.pickup_address or "").strip()
            cleaned["delivery_city"] = ""
            cleaned["delivery_city_ref"] = ""
            cleaned["delivery_branch"] = address
            cleaned["delivery_branch_ref"] = ""
            cleaned["delivery_address"] = address
        elif method == DeliveryMethod.TAXI:
            if not shipping.taxi_enabled:
                self.add_error("delivery_method", _("Доставка таксі тимчасово недоступна."))
            address = (cleaned.get("delivery_address") or "").strip()
            if not address:
                self.add_error("delivery_address", _("Вкажіть адресу для таксі."))
            cleaned["delivery_city"] = cleaned.get("delivery_city") or ""
            cleaned["delivery_city_ref"] = ""
            cleaned["delivery_branch"] = address
            cleaned["delivery_branch_ref"] = ""
            cleaned["delivery_address"] = address

        return cleaned
