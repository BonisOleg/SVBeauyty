from decimal import ROUND_HALF_UP, Decimal

import django.core.validators
from django.db import migrations, models


def _percent_for_amount(retail, target, step):
    """Підібрати відсоток, який після округлення дає поточну акційну суму."""
    from apps.pricing.services import personal_sale_amount

    retail = Decimal(retail)
    target = Decimal(target).quantize(Decimal("0.01"))
    raw = (retail - target) / retail * Decimal("100")
    center = int((raw * 100).to_integral_value(rounding=ROUND_HALF_UP))
    for delta in range(0, 300):
        candidates = (center,) if delta == 0 else (center + delta, center - delta)
        for cents in candidates:
            if cents <= 0 or cents > 9900:
                continue
            percent = (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))
            amount = personal_sale_amount(retail, percent, step)
            if amount == target:
                return percent
    fallback = raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if fallback <= 0:
        return Decimal("0.00")
    if fallback > 99:
        return Decimal("99.00")
    return fallback


def copy_sale_price_to_percent(apps, schema_editor):
    Variant = apps.get_model("catalog", "Variant")
    PricingSettings = apps.get_model("pricing", "PricingSettings")
    from apps.pricing.services import personal_sale_amount

    conf = PricingSettings.objects.order_by("pk").first()
    step = Decimal(getattr(conf, "rounding_step", None) or "1.00")
    for variant in Variant.objects.all().iterator():
        retail = Decimal(variant.price_uah or 0)
        sale = Decimal(variant.sale_price_uah or 0)
        if retail > 0 and sale > 0 and sale < retail:
            percent = _percent_for_amount(retail, sale, step)
            amount = personal_sale_amount(retail, percent, step)
            variant.sale_percent = percent
            variant.sale_price_uah = amount if amount is not None else Decimal("0.00")
        else:
            variant.sale_percent = Decimal("0.00")
            if sale != 0:
                variant.sale_price_uah = Decimal("0.00")
        variant.save(update_fields=["sale_percent", "sale_price_uah"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0014_product_usage"),
        ("pricing", "0004_global_sale_and_price_source_len"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="sale_percent",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                help_text=(
                    "Для гостей і звичайних клієнтів. 20 = мінус 20% від роздрібної, "
                    "округлення як у «Ціни та умови». 0 — без акції. Косметологи бачать pro-ціну."
                ),
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(99),
                ],
                verbose_name="Акційна знижка, %",
            ),
        ),
        migrations.AlterField(
            model_name="variant",
            name="sale_price_uah",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                help_text="Рахується з відсотка знижки. На сайті не редагується вручну.",
                max_digits=10,
                verbose_name="Акційна ціна, грн",
            ),
        ),
        migrations.RunPython(copy_sale_price_to_percent, migrations.RunPython.noop),
    ]
