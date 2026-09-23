from decimal import Decimal

from django import forms

from apps.catalog.models import Variant

PRICE_FIELDS = {
    "price_uah": "price_is_manual",
    "price_pro_uah": "price_pro_is_manual",
}


class VariantAdminForm(forms.ModelForm):
    """Ручне редагування ціни автоматично вмикає ручний режим для цього поля."""

    class Meta:
        model = Variant
        exclude = ["sale_price_uah"]

    def clean(self):
        data = super().clean()
        for price_field, flag_field in PRICE_FIELDS.items():
            if price_field not in self.fields:
                continue
            if data.get(price_field) in (None, ""):
                data[price_field] = Decimal("0.00")
            elif price_field in self.changed_data and not data.get(flag_field):
                data[flag_field] = True

        percent = data.get("sale_percent")
        if percent in (None, ""):
            data["sale_percent"] = Decimal("0.00")
        return data
