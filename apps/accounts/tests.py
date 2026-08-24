from django.test import TestCase
from django.urls import reverse

from apps.accounts.admin import CosmetologistRequestAdmin
from apps.accounts.models import ClientType, CosmetologistRequest, RequestStatus, User


class RegistrationTests(TestCase):
    def test_register_creates_regular_client(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Оля",
                "last_name": "Тест",
                "email": "New@Test.Local",
                "phone": "+380671234567",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
                "gdpr_accepted": "on",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        user = User.objects.get()
        self.assertEqual(user.email, "new@test.local")
        self.assertEqual(user.client_type, ClientType.REGULAR)

    def test_login_is_case_insensitive(self):
        User.objects.create_user("user@test.local", "Pass12345!")
        response = self.client.post(
            reverse("accounts:login"), {"username": "USER@test.local", "password": "Pass12345!"}
        )
        self.assertEqual(response.status_code, 302)


class CosmetologistStatusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cosmo@test.local", "Pass12345!")
        self.client.force_login(self.user)

    def test_request_sets_pending_not_pro(self):
        self.client.post(
            reverse("accounts:cosmetologist"),
            {"full_name": "Ірина Тест", "phone": "+380671234567", "workplace": "Салон", "comment": ""},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.client_type, ClientType.PENDING)
        self.assertFalse(self.user.is_pro)

    def test_client_type_cannot_be_set_from_frontend(self):
        self.client.post(
            reverse("accounts:profile"),
            {"first_name": "Оля", "last_name": "Тест", "phone": "+380671234567",
             "client_type": ClientType.COSMETOLOGIST},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.client_type, ClientType.REGULAR)

    def test_admin_approval_grants_pro_status(self):
        request_obj = CosmetologistRequest.objects.create(
            user=self.user, full_name="Ірина Тест", phone="+380671234567"
        )
        admin = CosmetologistRequestAdmin(CosmetologistRequest, None)
        admin.message_user = lambda *args, **kwargs: None
        admin.approve_requests(None, CosmetologistRequest.objects.filter(pk=request_obj.pk))

        self.user.refresh_from_db()
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, RequestStatus.APPROVED)
        self.assertTrue(self.user.is_pro)
        self.assertIsNotNone(self.user.client_type_changed_at)


class CabinetAccessTests(TestCase):
    def test_cabinet_requires_login(self):
        for name in ("accounts:profile", "accounts:orders", "accounts:loyalty"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response["Location"])
