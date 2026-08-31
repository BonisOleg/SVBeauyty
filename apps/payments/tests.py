from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.payments.services import available_methods, build_liqpay_payload, liqpay_enabled


class LiqPayPayloadTests(SimpleTestCase):
    @override_settings(LIQPAY_ENABLED=False, LIQPAY_PUBLIC_KEY="", LIQPAY_PRIVATE_KEY="")
    def test_disabled_without_keys(self):
        self.assertFalse(liqpay_enabled())
        codes = [m.code for m in available_methods()]
        self.assertNotIn("liqpay", codes)

    @override_settings(
        LIQPAY_ENABLED=True,
        LIQPAY_PUBLIC_KEY="sandbox_i00000000000",
        LIQPAY_PRIVATE_KEY="sandbox_a000000000000000000000000000000000000000",
    )
    def test_payload_for_thanks_button(self):
        self.assertTrue(liqpay_enabled())
        self.assertIn("liqpay", [m.code for m in available_methods()])
        order = SimpleNamespace(number="SV-TEST-1", total_uah=Decimal("250.00"))
        payload = build_liqpay_payload(order)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["checkout_url"], "https://www.liqpay.ua/api/3/checkout")
        self.assertTrue(payload["data"])
        self.assertTrue(payload["signature"])
