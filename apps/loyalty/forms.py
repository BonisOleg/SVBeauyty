from django import forms
from django.utils.translation import gettext_lazy as _


class AdjustLoyaltyPointsForm(forms.Form):
    OPERATION_CREDIT = "credit"
    OPERATION_DEBIT = "debit"
    OPERATION_CHOICES = [
        (OPERATION_CREDIT, _("Нарахувати")),
        (OPERATION_DEBIT, _("Списати")),
    ]

    operation = forms.ChoiceField(label=_("Операція"), choices=OPERATION_CHOICES)
    points = forms.IntegerField(label=_("Кількість балів"), min_value=1)
    comment = forms.CharField(
        label=_("Коментар"),
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": _("Причина зміни балансу")}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control = (
            "border border-base-200 bg-white font-medium px-3 py-2 rounded w-full "
            "focus:outline-none dark:bg-base-900 dark:border-base-700"
        )
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} {control}".strip()
            field.widget.attrs.setdefault("id", f"id_{name}")
