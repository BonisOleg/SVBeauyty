from django.test import TestCase, override_settings

from apps.shipping.models import NPCity, NPWarehouse, ShippingSettings
from apps.shipping.novaposhta import get_branches, search_cities
from apps.shipping.sync import _pages


class CityRankTests(TestCase):
    def setUp(self):
        ShippingSettings.objects.update_or_create(pk=1, defaults={"use_test_data": False, "np_api_key": "key"})
        kyiv = NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        NPCity.objects.create(ref="village", name="Андріївка (Київська обл.)", area="Київська")
        NPWarehouse.objects.create(
            ref="branch", city=kyiv, number="2", description="Відділення №2", category="Branch"
        )
        NPWarehouse.objects.create(
            ref="postomat", city=kyiv, number="1", description="Поштомат №1", category="Postomat"
        )
        NPWarehouse.objects.create(
            ref="cargo", city=kyiv, number="9", description="Вантажне", category="Cargo"
        )

    def test_kyiv_query_ranks_the_city_first(self):
        rows = search_cities("київ")
        self.assertEqual(rows[0]["name"], "Київ")
        self.assertGreater(len(rows), 1)

    def test_short_query_is_empty(self):
        self.assertEqual(search_cities("к"), [])
        self.assertEqual(search_cities(""), [])

    def test_branches_skip_cargo_and_put_postomats_last(self):
        rows = get_branches("kyiv")
        self.assertEqual([row["ref"] for row in rows], ["branch", "postomat"])


@override_settings(NOVAPOSHTA_API_KEY="")
class FixtureFallbackTests(TestCase):
    def test_fixture_when_directory_and_key_are_empty(self):
        ShippingSettings.objects.update_or_create(pk=1, defaults={"use_test_data": False, "np_api_key": ""})
        rows = search_cities("київ")
        self.assertEqual(rows[0]["ref"], "city-kyiv")

    def test_admin_key_does_not_use_fixture_before_sync(self):
        ShippingSettings.objects.update_or_create(pk=1, defaults={"use_test_data": False, "np_api_key": "from-admin"})
        self.assertEqual(search_cities("київ"), [])


class SyncPageTests(TestCase):
    def test_page_is_sent_as_string(self):
        calls = []

        def fake_call(model, method, props, *, timeout):
            calls.append(props)
            return []

        from apps.shipping import sync

        original = sync.api_call
        sync.api_call = fake_call
        try:
            list(_pages("Address", "getCities"))
        finally:
            sync.api_call = original
        self.assertEqual(calls[0]["Page"], "1")
        self.assertEqual(calls[0]["Limit"], "500")
        self.assertIsInstance(calls[0]["Page"], str)
