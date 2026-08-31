"""Довідник характеристик для фільтрів каталогу + прив’язка до товарів (seed)."""

ATTRIBUTE_GROUPS = [
    {
        "slug": "age",
        "name_uk": "За віком",
        "name_ru": "По возрасту",
        "sort_order": 10,
    },
    {
        "slug": "skin_type",
        "name_uk": "За типом шкіри",
        "name_ru": "По типу кожи",
        "sort_order": 20,
    },
    {
        "slug": "skin_condition",
        "name_uk": "За станом шкіри",
        "name_ru": "По состоянию кожи",
        "sort_order": 30,
    },
    {
        "slug": "ingredient",
        "name_uk": "Інгредієнти",
        "name_ru": "Ингредиенты",
        "sort_order": 40,
    },
]

ATTRIBUTES = [
    # age
    {"group": "age", "slug": "18-plus", "name_uk": "18+", "name_ru": "18+", "sort_order": 10},
    {"group": "age", "slug": "25-plus", "name_uk": "25+", "name_ru": "25+", "sort_order": 20},
    {"group": "age", "slug": "35-plus", "name_uk": "35+", "name_ru": "35+", "sort_order": 30},
    {"group": "age", "slug": "45-plus", "name_uk": "45+", "name_ru": "45+", "sort_order": 40},
    {"group": "age", "slug": "50-plus", "name_uk": "50+", "name_ru": "50+", "sort_order": 50},
    # skin_type
    {"group": "skin_type", "slug": "normal", "name_uk": "Нормальна", "name_ru": "Нормальная", "sort_order": 10},
    {"group": "skin_type", "slug": "dry", "name_uk": "Суха", "name_ru": "Сухая", "sort_order": 20},
    {"group": "skin_type", "slug": "oily", "name_uk": "Жирна", "name_ru": "Жирная", "sort_order": 30},
    {"group": "skin_type", "slug": "combination", "name_uk": "Комбінована", "name_ru": "Комбинированная", "sort_order": 40},
    {"group": "skin_type", "slug": "sensitive", "name_uk": "Чутлива", "name_ru": "Чувствительная", "sort_order": 50},
    {"group": "skin_type", "slug": "dehydrated", "name_uk": "Зневоднена", "name_ru": "Обезвоженная", "sort_order": 60},
    # skin_condition
    {"group": "skin_condition", "slug": "acne", "name_uk": "Акне", "name_ru": "Акне", "sort_order": 10},
    {"group": "skin_condition", "slug": "pigmentation", "name_uk": "Пігментація", "name_ru": "Пигментация", "sort_order": 20},
    {"group": "skin_condition", "slug": "wrinkles", "name_uk": "Зморшки", "name_ru": "Морщины", "sort_order": 30},
    {"group": "skin_condition", "slug": "pores", "name_uk": "Розширені пори", "name_ru": "Расширенные поры", "sort_order": 40},
    {"group": "skin_condition", "slug": "dullness", "name_uk": "Тьмяність", "name_ru": "Тусклость", "sort_order": 50},
    {"group": "skin_condition", "slug": "loss-of-firmness", "name_uk": "Втрата пружності", "name_ru": "Потеря упругости", "sort_order": 60},
    # ingredient
    {"group": "ingredient", "slug": "niacinamide", "name_uk": "Ніацинамід", "name_ru": "Ниацинамид", "sort_order": 10},
    {"group": "ingredient", "slug": "retinol", "name_uk": "Ретинол", "name_ru": "Ретинол", "sort_order": 20},
    {"group": "ingredient", "slug": "vitamin-c", "name_uk": "Вітамін C", "name_ru": "Витамин C", "sort_order": 30},
    {"group": "ingredient", "slug": "hyaluronic-acid", "name_uk": "Гіалуронова кислота", "name_ru": "Гиалуроновая кислота", "sort_order": 40},
    {"group": "ingredient", "slug": "peptides", "name_uk": "Пептиди", "name_ru": "Пептиды", "sort_order": 50},
    {"group": "ingredient", "slug": "aha-bha", "name_uk": "AHA/BHA кислоти", "name_ru": "AHA/BHA кислоты", "sort_order": 60},
    {"group": "ingredient", "slug": "centella", "name_uk": "Центелла", "name_ru": "Центелла", "sort_order": 70},
    {"group": "ingredient", "slug": "spf-filters", "name_uk": "SPF-фільтри", "name_ru": "SPF-фильтры", "sort_order": 80},
]

# Детерміновані набори slug-ів атрибутів для товарів (за slug товару).
# Якщо slug немає в мапі — призначаємо за індексом у каталозі.
PRODUCT_ATTRIBUTES = {
    "soft-fermentativnyi-pilinh": ["25-plus", "combination", "acne", "dullness", "aha-bha"],
    "enzymna-pilinh-skatka": ["18-plus", "oily", "pores", "acne", "aha-bha"],
    "salitsylovo-enzymnyi-pilinh": ["25-plus", "oily", "acne", "pores", "aha-bha"],
    "hidrofilne-mylo": ["18-plus", "normal", "sensitive", "dehydrated", "centella"],
    "probiotychnyi-hel-skin-capital": ["25-plus", "sensitive", "dehydrated", "dullness", "centella"],
    "toner-filer": ["25-plus", "dehydrated", "dullness", "hyaluronic-acid", "peptides"],
    "centella-supreme-toner": ["18-plus", "sensitive", "dehydrated", "centella", "niacinamide"],
    "tonik-ana": ["25-plus", "combination", "dullness", "pigmentation", "aha-bha"],
    "probiotychnyi-serum-skin-capital": ["25-plus", "sensitive", "dehydrated", "centella", "peptides"],
    "syrovatka-z-niatsynamidom": ["25-plus", "oily", "pores", "acne", "niacinamide"],
    "oximony-nad-serum": ["35-plus", "normal", "wrinkles", "loss-of-firmness", "peptides"],
    "krem-syrovatka-skin-revolt": ["35-plus", "dry", "wrinkles", "loss-of-firmness", "retinol"],
    "maska-ana": ["25-plus", "combination", "dullness", "pigmentation", "aha-bha"],
    "maska-yogurtene": ["18-plus", "dry", "dehydrated", "sensitive", "hyaluronic-acid"],
    "maska-relift": ["45-plus", "dry", "wrinkles", "loss-of-firmness", "peptides"],
    "krem-ultra-aqua": ["25-plus", "dehydrated", "dry", "hyaluronic-acid", "niacinamide"],
    "dennyi-krem-focus-super-lift": ["45-plus", "normal", "wrinkles", "loss-of-firmness", "peptides"],
    "centella-supreme-krem-hel": ["25-plus", "sensitive", "dehydrated", "centella", "niacinamide"],
    "peptydnyi-krem-pid-ochi": ["35-plus", "normal", "wrinkles", "peptides", "hyaluronic-acid"],
    "alternatyvni-patchi-dlya-ochei": ["25-plus", "dehydrated", "dullness", "hyaluronic-acid", "peptides"],
    "zvolozhuyuchyi-krem-defense-spf50": ["25-plus", "normal", "dry", "spf-filters", "hyaluronic-acid"],
    "matuyuchyi-krem-defense-spf50": ["18-plus", "oily", "combination", "pores", "spf-filters"],
}

FALLBACK_SETS = [
    ["18-plus", "normal", "dullness", "niacinamide"],
    ["25-plus", "combination", "acne", "aha-bha"],
    ["35-plus", "dry", "wrinkles", "peptides"],
    ["45-plus", "sensitive", "loss-of-firmness", "retinol"],
    ["25-plus", "oily", "pores", "vitamin-c"],
    ["50-plus", "dehydrated", "pigmentation", "hyaluronic-acid"],
]
