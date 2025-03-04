"""
Конфигурация для демо-заявок (прямой импорт)
"""

# Шаблоны демо-заявок по категориям
DEMO_REQUEST_TEMPLATES = {
    "Ремонт квартир": [
        "Нужен косметический ремонт в однокомнатной квартире.",
        "Требуется капитальный ремонт в новостройке.",
        "Интересует ремонт ванной комнаты под ключ.",
        "Нужна консультация по ремонту кухни."
    ],
    "Сантехника": [
        "Требуется установка унитаза и раковины в ванной комнате.",
        "Нужно заменить смеситель на кухне.",
        "Протекает труба под раковиной, требуется срочный ремонт.",
        "Интересует установка душевой кабины вместо ванны."
    ],
    "Электрика": [
        "Нужно заменить проводку в квартире.",
        "Требуется установка розеток и выключателей в новой квартире.",
        "Не работает свет в ванной, нужен электрик.",
        "Интересует монтаж системы умного дома."
    ],
    "Клининг": [
        "Нужна генеральная уборка квартиры после ремонта.",
        "Требуется регулярная уборка офиса.",
        "Интересует мытье окон в частном доме.",
        "Нужна химчистка мягкой мебели и ковров."
    ],
    "Грузоперевозки": [
        "Нужно перевезти мебель при переезде.",
        "Требуется доставка строительных материалов.",
        "Интересует перевозка крупногабаритной техники.",
        "Нужны грузчики для переезда офиса."
    ],
    "Строительство": [
        "Интересует строительство дачного домика.",
        "Нужна консультация по строительству гаража.",
        "Требуется возведение забора вокруг участка.",
        "Планирую строительство бани, нужна консультация."
    ],
    "Другое": [
        "Нужна консультация специалиста.",
        "Требуется оценка стоимости работ.",
        "Интересуют услуги по благоустройству территории.",
        "Нужна помощь с установкой бытовой техники."
    ]
}

# Демо-клиенты
DEMO_CLIENTS = [
    ("Иван Петров", "+7999123456"),
    ("Мария Сидорова", "+7999234567"),
    ("Алексей Иванов", "+7999345678"),
    ("Елена Смирнова", "+7999456789"),
    ("Дмитрий Козлов", "+7999567890"),
    ("Ольга Новикова", "+7999678901"),
    ("Сергей Морозов", "+7999789012"),
    ("Анна Волкова", "+7999890123")
]

# Интервалы генерации демо-заявок (в секундах)
DEMO_GENERATION_INTERVALS = {
    "min": 1800,  # 30 минут
    "max": 3600   # 1 час
}

# Настройки распределения демо-заявок
DEMO_DISTRIBUTION_SETTINGS = {
    "max_distributions_per_request": 3,
    "expiration_hours": 24  # Время жизни демо-заявки в часах
} 