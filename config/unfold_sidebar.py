from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


def navigation(request):
    """Меню Unfold: без дублів «розділ = єдина модель»."""
    return [
        {
            "title": _("Каталог"),
            "separator": False,
            "items": [
                {
                    "title": _("Товари"),
                    "icon": "inventory_2",
                    "link": reverse_lazy("admin:catalog_product_changelist"),
                },
                {
                    "title": _("Категорії"),
                    "icon": "category",
                    "link": reverse_lazy("admin:catalog_category_changelist"),
                },
                {
                    "title": _("Бренди"),
                    "icon": "storefront",
                    "link": reverse_lazy("admin:catalog_brand_changelist"),
                },
                {
                    "title": _("Варіанти (обʼєми)"),
                    "icon": "straighten",
                    "link": reverse_lazy("admin:catalog_variant_changelist"),
                },
            ],
        },
        {
            "title": _("Продажі"),
            "separator": True,
            "items": [
                {
                    "title": _("Замовлення"),
                    "icon": "shopping_bag",
                    "link": reverse_lazy("admin:commerce_order_changelist"),
                },
                {
                    "title": _("Кошики"),
                    "icon": "shopping_cart",
                    "link": reverse_lazy("admin:commerce_cart_changelist"),
                },
            ],
        },
        {
            "title": _("Клієнти"),
            "separator": True,
            "items": [
                {
                    "title": _("Клієнти"),
                    "icon": "group",
                    "link": reverse_lazy("admin:accounts_user_changelist"),
                },
                {
                    "title": _("Заявки косметологів"),
                    "icon": "badge",
                    "link": reverse_lazy("admin:accounts_cosmetologistrequest_changelist"),
                },
            ],
        },
        {
            "title": _("Контент"),
            "separator": True,
            "items": [
                {
                    "title": _("Сторінки"),
                    "icon": "article",
                    "link": reverse_lazy("admin:content_page_changelist"),
                },
                {
                    "title": _("Банери"),
                    "icon": "image",
                    "link": reverse_lazy("admin:content_banner_changelist"),
                },
                {
                    "title": _("Налаштування сайту"),
                    "icon": "settings",
                    "link": reverse_lazy("admin:content_sitesettings_changelist"),
                },
            ],
        },
        {
            "title": _("Налаштування"),
            "separator": True,
            "items": [
                {
                    "title": _("Доставка"),
                    "icon": "local_shipping",
                    "link": reverse_lazy("admin:shipping_shippingsettings_changelist"),
                },
                {
                    "title": _("Ціни та умови"),
                    "icon": "payments",
                    "link": reverse_lazy("admin:pricing_pricingsettings_changelist"),
                },
                {
                    "title": _("Програма лояльності"),
                    "icon": "stars",
                    "link": reverse_lazy("admin:loyalty_loyaltysettings_changelist"),
                },
                {
                    "title": _("Бонусні рахунки"),
                    "icon": "account_balance_wallet",
                    "link": reverse_lazy("admin:loyalty_loyaltyaccount_changelist"),
                },
                {
                    "title": _("Бонусні операції"),
                    "icon": "receipt_long",
                    "link": reverse_lazy("admin:loyalty_loyaltytransaction_changelist"),
                },
            ],
        },
        {
            "title": _("Підтримка"),
            "separator": True,
            "items": [
                {
                    "title": _("Чат — діалоги"),
                    "icon": "chat",
                    "link": reverse_lazy("admin:chat_chatsession_changelist"),
                },
                {
                    "title": _("Групи доступу"),
                    "icon": "admin_panel_settings",
                    "link": reverse_lazy("admin:auth_group_changelist"),
                },
            ],
        },
    ]
