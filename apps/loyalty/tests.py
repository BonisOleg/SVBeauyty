from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.loyalty.models import LoyaltyAccount, LoyaltyTransaction, TransactionKind
from apps.loyalty.services import get_available_balance, get_balance


User = get_user_model()


class LoyaltyAdminAdjustTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@test.local", "Pass12345!")
        self.client_user = User.objects.create_user("client@test.local", "Pass12345!")
        self.account = LoyaltyAccount.objects.create(user=self.client_user, balance=0)
        self.client.force_login(self.admin)
        self.url = reverse(
            "admin:loyalty_loyaltyaccount_adjust_points",
            args=[self.account.pk],
        )

    def test_credit_points_via_admin(self):
        response = self.client.post(
            self.url,
            {
                "operation": "credit",
                "points": 150,
                "comment": "Компенсація за затримку",
            },
        )
        self.assertRedirects(
            response,
            reverse("admin:loyalty_loyaltyaccount_change", args=[self.account.pk]),
        )
        self.assertEqual(get_balance(self.client_user), 150)
        self.assertEqual(get_available_balance(self.client_user), 150)
        txn = LoyaltyTransaction.objects.get()
        self.assertEqual(txn.kind, TransactionKind.MANUAL)
        self.assertEqual(txn.points, 150)
        self.assertIn("admin@test.local", txn.comment)

    def test_debit_points_via_admin(self):
        self.client.post(
            self.url,
            {"operation": "credit", "points": 100, "comment": "Старт"},
        )
        response = self.client.post(
            self.url,
            {"operation": "debit", "points": 40, "comment": "Корекція"},
        )
        self.assertRedirects(
            response,
            reverse("admin:loyalty_loyaltyaccount_change", args=[self.account.pk]),
        )
        self.assertEqual(get_balance(self.client_user), 60)

    def test_debit_more_than_balance_fails(self):
        response = self.client.post(
            self.url,
            {"operation": "debit", "points": 10, "comment": "Помилка"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_balance(self.client_user), 0)
        self.assertFalse(LoyaltyTransaction.objects.exists())
