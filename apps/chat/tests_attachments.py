from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.accounts.models import User
from apps.chat.models import ChatAttachment


def _png(name="pay.png"):
    buf = BytesIO()
    Image.new("RGB", (16, 16), (200, 20, 20)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def _pdf(name="cert.pdf", body=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"):
    return SimpleUploadedFile(name, body, content_type="application/pdf")


class ChatAttachmentTests(TestCase):
    def setUp(self):
        self.client.post(
            reverse("chat:send"),
            {"name": "Оля", "phone": "+380671112233", "text": "старт"},
        )

    def test_image_is_stored_as_webp_and_owner_can_open_it(self):
        response = self.client.post(reverse("chat:send"), {"text": "оплата", "files": _png()})
        self.assertEqual(response.status_code, 200)
        attachment = ChatAttachment.objects.get()
        self.assertEqual(attachment.kind, "image")
        self.assertTrue(attachment.original_name.endswith(".webp"))
        self.assertTrue(attachment.file.name.endswith(".webp"))

        opened = self.client.get(reverse("chat:file", args=[attachment.public_id]))
        self.assertEqual(opened.status_code, 200)
        self.assertEqual(opened["Content-Type"], "image/webp")
        self.assertIn("nosniff", opened["X-Content-Type-Options"])

    def test_other_session_cannot_download(self):
        self.client.post(reverse("chat:send"), {"text": "", "files": _png()})
        attachment = ChatAttachment.objects.get()
        outsider = self.client_class()
        outsider.get(reverse("chat:history"))
        denied = outsider.get(reverse("chat:file", args=[attachment.public_id]))
        self.assertEqual(denied.status_code, 404)

    def test_pdf_and_rules_rejection(self):
        ok = self.client.post(reverse("chat:send"), {"text": "", "files": _pdf()})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ChatAttachment.objects.get().kind, "pdf")

        bad = self.client.post(
            reverse("chat:send"),
            {"text": "", "files": SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")},
        )
        self.assertEqual(bad.status_code, 400)
        self.assertIn("WebP", bad.content.decode())

        too_many = self.client.post(
            reverse("chat:send"),
            {"text": "x", "files": [_png("a.png"), _png("b.png"), _png("c.png"), _png("d.png")]},
        )
        self.assertEqual(too_many.status_code, 400)

    def test_staff_reply_with_pdf(self):
        from apps.chat.models import ChatSession

        staff = User.objects.create_superuser("mgr@test.local", "Pass12345!")
        session = ChatSession.objects.get()
        admin = self.client_class()
        admin.force_login(staff)
        response = admin.post(
            reverse("admin:chat_chatsession_reply", args=[session.pk]),
            {"text": "сертифікат", "files": _pdf("cert.pdf")},
        )
        self.assertEqual(response.status_code, 200, response.content)
        attachment = ChatAttachment.objects.get()
        opened = admin.get(reverse("chat:file", args=[attachment.public_id]))
        self.assertEqual(opened.status_code, 200)
        self.assertIn("inline", opened["Content-Disposition"])
        saved = admin.get(reverse("chat:file", args=[attachment.public_id]) + "?download=1")
        self.assertIn("attachment", saved["Content-Disposition"])

    def test_widget_shows_rules_and_clip(self):
        home = self.client.get(reverse("core:home"))
        html = home.content.decode()
        self.assertIn("chat__clip", html)
        self.assertIn("Зображення зберігаються у WebP", html)
        self.assertIn('name="files"', html)
