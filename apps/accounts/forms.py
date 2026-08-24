from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import CosmetologistRequest
from apps.accounts.validators import validate_cosmetologist_document

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"), widget=forms.EmailInput(attrs={"autocomplete": "email", "inputmode": "email"})
    )

    error_messages = {
        "invalid_login": _("Невірний email або пароль."),
        "inactive": _("Обліковий запис вимкнено."),
    }


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_("Пароль"), widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), min_length=8
    )
    password2 = forms.CharField(
        label=_("Повторіть пароль"), widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    gdpr_accepted = forms.BooleanField(label=_("Погоджуюсь на обробку персональних даних"))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        labels = {
            "first_name": _("Ім'я"),
            "last_name": _("Прізвище"),
            "email": _("Email"),
            "phone": _("Телефон"),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Такий email вже зареєстровано."))
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", _("Паролі не збігаються."))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]
        labels = {"first_name": _("Ім'я"), "last_name": _("Прізвище"), "phone": _("Телефон")}


class CosmetologistRequestForm(forms.ModelForm):
    class Meta:
        model = CosmetologistRequest
        fields = ["full_name", "phone", "workplace", "document", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}

    def clean_document(self):
        document = self.cleaned_data.get("document")
        if document:
            validate_cosmetologist_document(document)
        return document
