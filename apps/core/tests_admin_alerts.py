from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import CosmetologistRequest, RequestStatus
from apps.chat.models import ChatMessage, ChatSession, MessageAuthor
from apps.commerce.models import Order, OrderStatus
from apps.core.admin_alerts import get_alert_counts, get_alerts_payload

User = get_user_model()


class AdminAlertsTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="manager@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client = Client()
        self.client.force_login(self.staff)

    def test_counts_and_endpoint(self):
        Order.objects.create(
            number="T-1",
            first_name="A",
            last_name="B",
            phone="+380501112233",
            status=OrderStatus.NEW,
            gdpr_accepted=True,
        )
        user = User.objects.create_user(email="c@example.com", password="pass12345")
        CosmetologistRequest.objects.create(
            user=user,
            full_name="Test Cosmet",
            phone="+380501112244",
            status=RequestStatus.NEW,
        )
        session = ChatSession.objects.create(session_key="k1", name="Guest")
        ChatMessage.objects.create(
            session=session,
            author=MessageAuthor.CUSTOMER,
            text="Hello",
            is_read=False,
        )

        counts = get_alert_counts()
        self.assertEqual(counts["orders"], 1)
        self.assertEqual(counts["requests"], 1)
        self.assertEqual(counts["messages"], 1)
        self.assertEqual(counts["total"], 3)

        payload = get_alerts_payload()
        self.assertEqual(len(payload["feed"]["orders"]), 1)
        self.assertEqual(len(payload["feed"]["requests"]), 1)
        self.assertEqual(len(payload["feed"]["messages"]), 1)

        res = self.client.get(reverse("admin_alerts"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
