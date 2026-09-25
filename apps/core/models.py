from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.utils import localized


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        abstract = True


class SeoModel(models.Model):
    seo_title_uk = models.CharField(_("SEO Title (укр)"), max_length=255, blank=True)
    seo_title_ru = models.CharField(_("SEO Title (рос)"), max_length=255, blank=True)
    seo_description_uk = models.TextField(_("SEO Description (укр)"), blank=True)
    seo_description_ru = models.TextField(_("SEO Description (рос)"), blank=True)

    class Meta:
        abstract = True

    @property
    def seo_title(self):
        return localized(self, "seo_title")

    @property
    def seo_description(self):
        return localized(self, "seo_description")


class PublishedModel(models.Model):
    is_active = models.BooleanField(_("Показувати на сайті"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Порядок"), default=100)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Одна єдина строка налаштувань."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj
