from django import forms
from django.utils.translation import gettext_lazy as _

from apps.commerce.models import PaymentMethod


class CheckoutForm(forms.Form):
    first_name = forms.CharField(label=_("Ім'я"), max_length=150)
    last_name = forms.CharField(label=_("Прізвище"), max_length=150)
    phone = forms.CharField(label=_("Телефон"), max_length=32)
    email = forms.EmailField(label=_("Email"), required=False)

    delivery_city = forms.CharField(label=_("Місто"), max_length=160)
    delivery_city_ref = forms.CharField(max_length=64, widget=forms.HiddenInput())
    delivery_branch = forms.CharField(label=_("Відділення Нової Пошти"), max_length=255)
    delivery_branch_ref = forms.CharField(max_length=64, widget=forms.HiddenInput())

    payment_method = forms.ChoiceField(label=_("Спосіб оплати"), choices=PaymentMethod.choices)
    comment = forms.CharField(label=_("Коментар"), required=False, widget=forms.Textarea(attrs={"rows": 3}))
    redeem_points = forms.IntegerField(label=_("Списати балів"), required=False, min_value=0)
    gdpr_accepted = forms.BooleanField(label=_("Погоджуюсь на обробку персональних даних"))

    def __init__(self, *args, allowed_methods=None, max_points=0, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_methods:
            self.fields["payment_method"].choices = [(m.code, m.label) for m in allowed_methods]
        self.max_points = max_points
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["email"].widget.attrs.update({"inputmode": "email", "autocomplete": "email"})

    def clean_phone(self):
        phone = "".join(ch for ch in self.cleaned_data["phone"] if ch.isdigit() or ch == "+")
        if len(phone.lstrip("+")) < 9:
            raise forms.ValidationError(_("Вкажіть коректний номер телефону."))
        return phone

    def clean_redeem_points(self):
        points = self.cleaned_data.get("redeem_points") or 0
        if points > self.max_points:
            raise forms.ValidationError(_("Доступно максимум %(n)s балів.") % {"n": self.max_points})
        return points
