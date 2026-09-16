from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.chat.business_hours import is_within_business_hours
from apps.chat.models import ChatMessage, MessageAuthor

KYIV = ZoneInfo("Europe/Kyiv")


class BusinessHoursTests(SimpleTestCase):
    def test_weekday_inside(self):
        # Wednesday 2026-09-16 12:00 Kyiv
        dt = datetime(2026, 9, 16, 12, 0, tzinfo=KYIV)
        self.assertTrue(is_within_business_hours(dt))

    def test_weekday_before_open(self):
        dt = datetime(2026, 9, 16, 8, 59, tzinfo=KYIV)
        self.assertFalse(is_within_business_hours(dt))

    def test_weekday_at_close(self):
        dt = datetime(2026, 9, 16, 18, 0, tzinfo=KYIV)
        self.assertFalse(is_within_business_hours(dt))

    def test_saturday_window(self):
        # Saturday 2026-09-19
        self.assertTrue(is_within_business_hours(datetime(2026, 9, 19, 10, 0, tzinfo=KYIV)))
        self.assertTrue(is_within_business_hours(datetime(2026, 9, 19, 14, 59, tzinfo=KYIV)))
        self.assertFalse(is_within_business_hours(datetime(2026, 9, 19, 15, 0, tzinfo=KYIV)))
        self.assertFalse(is_within_business_hours(datetime(2026, 9, 19, 9, 59, tzinfo=KYIV)))

    def test_sunday_closed(self):
        dt = datetime(2026, 9, 20, 12, 0, tzinfo=KYIV)
        self.assertFalse(is_within_business_hours(dt))


class AutoReplySendTests(TestCase):
    def setUp(self):
        self.client = Client()
        # ensure session
        self.client.get("/")

    def _send(self, text, **extra):
        return self.client.post(
            reverse("chat:send"),
            data={"text": text, "name": "Тест", "phone": "+380501112233", **extra},
            HTTP_HX_REQUEST="true",
        )

    @patch("apps.chat.views.is_within_business_hours", return_value=False)
    def test_first_message_outside_hours_gets_auto_reply(self, _mock):
        res = self._send("привіт")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Дякуємо! Повідомлення отримано")
        self.assertEqual(ChatMessage.objects.filter(author=MessageAuthor.MANAGER).count(), 1)

        res2 = self._send("ще раз")
        self.assertEqual(res2.status_code, 200)
        self.assertNotContains(res2, "Дякуємо! Повідомлення отримано")
        self.assertEqual(ChatMessage.objects.filter(author=MessageAuthor.MANAGER).count(), 1)

    @patch("apps.chat.views.is_within_business_hours", return_value=True)
    def test_first_message_inside_hours_no_auto_reply(self, _mock):
        res = self._send("привіт")
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "Дякуємо! Повідомлення отримано")
        self.assertEqual(ChatMessage.objects.filter(author=MessageAuthor.MANAGER).count(), 0)
