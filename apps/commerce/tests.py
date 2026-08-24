from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import ClientType, User
from apps.catalog.forms import VariantAdminForm
from apps.catalog.models import Brand, Category, Product, Variant
from apps.commerce.models import Order, OrderStatus
from apps.content.models import SiteSettings
from apps.loyalty import services as loyalty
from apps.loyalty.models import LoyaltySettings, TransactionKind
from apps.pricing import services as pricing_services
from apps.pricing.models import PricingSettings
from apps.pricing.services import PRO_AUTO, PRO_MANUAL, RETAIL, get_price


class ShopTestCase(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Cure Skin", slug="cure-skin")
        self.category = Category.objects.create(name_uk="Сироватки", slug="syrovatky")
        self.product = Product.objects.create(
            brand=self.brand, category=self.category, name_uk="Тест-серум", slug="test-serum"
        )
        pricing = PricingSettings.get_solo()
        pricing.retail_markup_percent = Decimal("100.00")
        pricing.pro_markup_percent = Decimal("40.00")
        pricing.rounding_step = "1.00"
        pricing.save()

        self.variant = Variant.objects.create(
            product=self.product,
            sku="T-001",
            volume="30 мл",
            purchase_price_uah=Decimal("500.00"),
            stock_qty=10,
        )

        settings_obj = SiteSettings.get_solo()
        settings_obj.manager_email = "manager@test.local"
        settings_obj.bank_iban = "UA123456789"
        settings_obj.bank_recipient = "ФОП Тест"
        settings_obj.bank_purpose_template = "Оплата замовлення {order_number}"
        settings_obj.save()

        self.regular = User.objects.create_user("client@test.local", "Pass12345!")
        self.pro = User.objects.create_user(
            "cosmo@test.local", "Pass12345!", client_type=ClientType.COSMETOLOGIST
        )

    def _checkout_payload(self, **overrides):
        payload = {
            "first_name": "Оля",
            "last_name": "Тест",
            "phone": "+380671234567",
            "email": "buyer@test.local",
            "delivery_city": "Київ",
            "delivery_city_ref": "city-kyiv",
            "delivery_branch": "Відділення №1",
            "delivery_branch_ref": "kyiv-1",
            "payment_method": "bank_details",
            "comment": "",
            "gdpr_accepted": "on",
        }
        payload.update(overrides)
        return payload


class PricingTests(ShopTestCase):
    def test_prices_are_calculated_from_purchase_price(self):
        self.assertEqual(self.variant.price_uah, Decimal("1000.00"))
        self.assertEqual(self.variant.price_pro_uah, Decimal("700.00"))

    def test_guest_and_regular_get_retail_price(self):
        for user in (None, self.regular):
            price = get_price(self.variant, user)
            self.assertEqual(price.amount, Decimal("1000.00"))
            self.assertEqual(price.source, RETAIL)

    def test_cosmetologist_gets_pro_price(self):
        price = get_price(self.variant, self.pro)
        self.assertEqual(price.amount, Decimal("700.00"))
        self.assertEqual(price.source, PRO_AUTO)

    def test_manual_price_survives_recalculation(self):
        self.variant.price_pro_uah = Decimal("750.00")
        self.variant.price_pro_is_manual = True
        self.variant.save()

        pricing_services.recalculate_all()
        self.variant.refresh_from_db()

        price = get_price(self.variant, self.pro)
        self.assertEqual(price.amount, Decimal("750.00"))
        self.assertEqual(price.source, PRO_MANUAL)

    def test_auto_price_follows_markup_change(self):
        conf = PricingSettings.get_solo()
        conf.retail_markup_percent = Decimal("150.00")
        conf.save()

        pricing_services.recalculate_all()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.price_uah, Decimal("1250.00"))

    def test_rounding_step_is_applied(self):
        conf = PricingSettings.get_solo()
        conf.retail_markup_percent = Decimal("33.00")
        conf.rounding_step = "10.00"
        conf.save()

        pricing_services.recalculate_all()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.price_uah, Decimal("670.00"))

    def test_editing_price_in_admin_switches_to_manual(self):
        form = VariantAdminForm(
            instance=self.variant,
            data={
                "product": self.product.id,
                "sku": self.variant.sku,
                "volume": self.variant.volume,
                "purchase_price_uah": "500.00",
                "price_uah": "1290.00",
                "price_pro_uah": "700.00",
                "stock_qty": 10,
                "sort_order": 0,
                "is_active": "on",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        variant = form.save()
        self.assertTrue(variant.price_is_manual)
        self.assertEqual(variant.price_uah, Decimal("1290.00"))
        self.assertFalse(variant.price_pro_is_manual)

    def test_pending_cosmetologist_still_pays_retail(self):
        self.regular.client_type = ClientType.PENDING
        self.regular.save()
        self.assertEqual(get_price(self.variant, self.regular).source, RETAIL)


class CartTests(ShopTestCase):
    def test_add_updates_counter_and_popup(self):
        response = self.client.post(
            reverse("commerce:cart_add"),
            {"variant_id": self.variant.id, "quantity": 2},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(response.json()["subtotal"], "2000.00")

    def test_quantity_is_capped_by_stock(self):
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 500})
        response = self.client.post(
            reverse("commerce:cart_add"),
            {"variant_id": self.variant.id, "quantity": 1},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.json()["count"], 10)

    def test_quantity_respects_max_qty_when_stock_allows(self):
        self.variant.stock_qty = 200
        self.variant.save(update_fields=["stock_qty"])
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 500})
        response = self.client.post(
            reverse("commerce:cart_add"),
            {"variant_id": self.variant.id, "quantity": 1},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.json()["count"], 99)


class CheckoutTests(ShopTestCase):
    def test_guest_order_snapshots_price_and_requisites(self):
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        response = self.client.post(reverse("commerce:checkout"), self._checkout_payload())

        order = Order.objects.get()
        self.assertRedirects(response, reverse("commerce:thanks", kwargs={"number": order.number}))
        self.assertEqual(order.status, OrderStatus.NEW)
        self.assertEqual(order.total_uah, Decimal("1000.00"))
        self.assertEqual(order.items.get().price_source, RETAIL)
        self.assertEqual(order.bank_details_snapshot["iban"], "UA123456789")
        self.assertIn(order.number, order.bank_details_snapshot["purpose"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.number, mail.outbox[0].subject)

    def test_cosmetologist_order_uses_pro_price(self):
        self.client.force_login(self.pro)
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        self.client.post(reverse("commerce:checkout"), self._checkout_payload())

        order = Order.objects.get()
        self.assertEqual(order.client_type, ClientType.COSMETOLOGIST)
        self.assertEqual(order.total_uah, Decimal("700.00"))
        item = order.items.get()
        self.assertEqual(item.price_source, PRO_AUTO)
        self.assertEqual(item.unit_purchase_price_uah, Decimal("500.00"))

    def test_order_decrements_stock(self):
        self.assertEqual(self.variant.stock_qty, 10)
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 2})
        self.client.post(reverse("commerce:checkout"), self._checkout_payload())
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 8)
        self.assertEqual(Order.objects.get().items.get().quantity, 2)

    def test_cannot_buy_more_than_stock(self):
        self.variant.stock_qty = 1
        self.variant.save(update_fields=["stock_qty"])
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 5})
        from apps.commerce.models import CartItem

        item = CartItem.objects.get()
        self.assertEqual(item.quantity, 1)

    def test_points_are_redeemed_and_capped(self):
        conf = LoyaltySettings.get_solo()
        conf.max_redeem_percent = Decimal("30.00")
        conf.save()
        loyalty.apply_transaction(self.regular, TransactionKind.MANUAL, 900, comment="старт")

        self.client.force_login(self.regular)
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        response = self.client.post(
            reverse("commerce:checkout"), self._checkout_payload(redeem_points=900)
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Доступно максимум 300")
        self.assertFalse(Order.objects.exists())

    def test_points_earned_after_order(self):
        self.client.force_login(self.regular)
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        self.client.post(reverse("commerce:checkout"), self._checkout_payload())

        # 1000 грн × 0.05 = 50 балів
        self.assertEqual(loyalty.get_balance(self.regular), 50)

    def test_gdpr_is_required(self):
        self.client.post(reverse("commerce:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        payload = self._checkout_payload()
        payload.pop("gdpr_accepted")
        response = self.client.post(reverse("commerce:checkout"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())


class LocaleTests(ShopTestCase):
    def test_both_languages_render_catalog(self):
        for code in ("uk", "ru"):
            response = self.client.get(f"/{code}/")
            self.assertEqual(response.status_code, 200)

    def test_root_redirects_to_default_language(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/uk/"))
