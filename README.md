# SVbeauty

Інтернет-магазин професійної косметики Cure Skin і Great Care.
Django 5 + PostgreSQL + HTMX-free vanilla JS, адмінка на Unfold.

## Що всередині

- Каталог з категоріями, брендами, варіантами (об'єм = ціна + артикул)
- **Дві ціни:** роздрібна та для косметологів (ручна ціна SKU або глобальний %)
- Кабінет клієнта: профіль, замовлення, бонуси, заявка на статус косметолога
- Програма лояльності: нарахування й списання балів з лімітом
- Кошик, checkout, Нова Пошта, реквізити ФОП з копіюванням у буфер
- Live-чат з історією в БД і листом менеджеру
- Дві мови інтерфейсу: `uk` (за замовчуванням) і `ru`
- SEO: мета-теги, `sitemap.xml`, `robots.txt`

## Локальний запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # для dev достатньо DB_ENGINE=sqlite

python3 manage.py migrate
python3 manage.py seed_demo   # 22 тестові SKU, 8 категорій, сторінки, налаштування
python3 manage.py createsuperuser
python3 manage.py compilemessages
python3 manage.py runserver
```

Сайт: http://127.0.0.1:8000/uk/ · Адмінка: http://127.0.0.1:8000/admin/

## Структура

```
config/settings/   base · develop · production · test
apps/
  core/            абстрактні моделі, context processors, головна
  accounts/        User (логін по email), типи клієнтів, заявки косметологів
  catalog/         Brand · Category · Product · Variant · ProductImage
  pricing/         PricingSettings + PricingService (єдине джерело ціни)
  loyalty/         бали: налаштування, рахунки, транзакції
  commerce/        кошик, замовлення, checkout, листи
  shipping/        Нова Пошта (API + тестовий довідник)
  payments/        способи оплати, слот LiqPay
  content/         налаштування сайту, сторінки, банери
  chat/            діалоги та повідомлення
  seo/             sitemaps, robots.txt
static/css/        base · components · pages (без збірника)
templates/         base + компоненти + сторінки
locale/uk|ru/      каталоги перекладів
```

Схема БД — `tables.md`.

## Ціни

У варіанта три ціни. Адміністратор вводить лише **закупівельну**, решта
рахується автоматично від націнок з розділу «Ціни та умови»:

| Поле | Як заповнюється |
|---|---|
| `purchase_price_uah` | вручну при додаванні товару; на сайті не показується |
| `price_uah` | закупівельна + `retail_markup_percent`, з округленням `rounding_step` |
| `price_pro_uah` | закупівельна + `pro_markup_percent`, показується косметологам |

Будь-яку з двох розрахованих цін можна перебити вручну: достатньо вписати
своє значення — прапорець `price_is_manual` / `price_pro_is_manual`
проставиться сам, і автоперерахунок таку ціну більше не чіпатиме.
Повернути на автомат — дією «Зняти ручний режим і перерахувати».

Перерахунок запускається при збереженні варіанта, при зміні націнок
у «Ціни та умови» і командою:

```bash
python3 manage.py recalc_prices          # тільки автоціни
python3 manage.py recalc_prices --force  # скинути ручний режим і перерахувати все
```

Статус `cosmetologist` проставляє **лише адміністратор** — у картці клієнта
або дією «Схвалити» у заявках. Форми фронтенду поле `client_type` не приймають.

## Тестові фото

До передачі реальних матеріалів каталог наповнений згенерованими заглушками:

```bash
python3 manage.py seed_images          # тільки там, де фото ще немає
python3 manage.py seed_images --force  # перегенерувати все
```

## Керування контентом

| Що | Де в адмінці |
|---|---|
| Товари, ціни, залишки | Каталог → Товари / Варіанти |
| Націнки, округлення, умови доставки | Ціни та умови |
| Бали: нарахування й ліміт списання | Лояльність → Програма лояльності |
| Реквізити ФОП, контакти, промо-смуга | Контент → Налаштування сайту |
| Тексти сторінок (uk/ru + окремо для pro) | Контент → Сторінки |
| Заявки косметологів | Клієнти → Заявки косметологів |
| Чат | Чат → Діалоги |
| API-ключ Нової Пошти | Доставка |

## Тести

```bash
python3 manage.py test apps --settings=config.settings.test
```

Покривають ціноутворення по ролях, кошик, checkout, бали, GDPR, дві мови,
права на зміну статусу косметолога.

## Переклади

Рядки інтерфейсу — українською в коді, російська в `locale/ru`.

```bash
python3 manage.py makemessages -l ru -l uk --ignore=staticfiles --ignore=media
python3 _reference/apply_ru_translations.py   # словник uk→ru
python3 manage.py compilemessages
```

Контент (назви товарів, описи, сторінки) перекладається в адмінці —
поля `_uk` / `_ru`. Слаг один на сутність, мова живе лише в префіксі URL.

## Продакшен

```bash
cp .env.example .env   # заповнити SECRET_KEY, ALLOWED_HOSTS, БД, SMTP
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Nginx-конфіг — `deploy/nginx/svbeauty.conf`, сертифікати через certbot
у `deploy/certbot/`.

## Не входить у цей реліз

Створення ТТН Нової Пошти, промокоди, відгуки, wishlist, порівняння,
інтеграція з CRM/1С, автоімпорт прайсів.
LiqPay підключається ключами в `.env` без правок коду.
