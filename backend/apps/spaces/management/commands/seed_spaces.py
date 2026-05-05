from django.core.management.base import BaseCommand
from apps.spaces.models import Amenity, Category, Space


SPACES = [
    {
        'name': 'Конференц-зал «Атлас»',
        'address': 'ул. Ленина, 12, эт. 3',
        'capacity': 30,
        'price_per_hour': 2500,
        'description': 'Просторный конференц-зал для презентаций и корпоративных мероприятий. Вмещает до 30 человек, оборудован проектором и маркерной доской.',
        'has_projector': True,
        'has_board': True,
        'has_wifi': True,
        'category': 'conference-hall',
        'amenities': ['projector', 'board', 'wifi'],
    },
    {
        'name': 'Переговорная комната «Ньютон»',
        'address': 'ул. Пушкина, 5, эт. 2',
        'capacity': 8,
        'price_per_hour': 900,
        'description': 'Уютная переговорная комната для небольших рабочих групп. Идеально для брифингов, интервью и онлайн-совещаний.',
        'has_projector': False,
        'has_board': True,
        'has_wifi': True,
        'category': 'meeting-room',
        'amenities': ['board', 'wifi'],
    },
    {
        'name': 'Открытое пространство «Лофт»',
        'address': 'пр. Победы, 88, эт. 5',
        'capacity': 50,
        'price_per_hour': 3800,
        'description': 'Открытое лофтовое пространство для масштабных мероприятий: воркшопов, хакатонов, тренингов. Есть сцена и проекционное оборудование.',
        'has_projector': True,
        'has_board': False,
        'has_wifi': True,
        'category': 'loft',
        'amenities': ['projector', 'wifi'],
    },
    {
        'name': 'Кабинет «Соло»',
        'address': 'ул. Мира, 3, здание Б',
        'capacity': 1,
        'price_per_hour': 400,
        'description': 'Изолированное рабочее место для одного человека. Подходит для сосредоточенной работы, онлайн-звонков или рабочего оффлайна.',
        'has_projector': False,
        'has_board': False,
        'has_wifi': True,
        'category': 'office',
        'amenities': ['wifi'],
    },
    {
        'name': 'Тренинговый класс «Старт»',
        'address': 'ул. Новаторов, 21, эт. 1',
        'capacity': 15,
        'price_per_hour': 1500,
        'description': 'Просторный класс для обучения и тренингов. Есть проектор, маркерная доска, расставленные столы для партнерской работы.',
        'has_projector': True,
        'has_board': True,
        'has_wifi': True,
        'category': 'training-room',
        'amenities': ['projector', 'board', 'wifi'],
    },
    {
        'name': 'Подиум «Премьер»',
        'address': 'пр. Суворова, 1',
        'capacity': 100,
        'price_per_hour': 8000,
        'description': 'Большой подиум для крупных мероприятий: конференций, выставок, презентаций. Полное мультимедийное оснащение, сцена с подиумом.',
        'has_projector': True,
        'has_board': False,
        'has_wifi': True,
        'category': 'event-hall',
        'amenities': ['projector', 'wifi'],
    },
]

CATEGORIES = {
    'meeting-room': 'Переговорная',
    'conference-hall': 'Конференц-зал',
    'loft': 'Лофт / Open space',
    'office': 'Кабинет',
    'training-room': 'Учебный класс',
    'event-hall': 'Подиум / Зал',
}

AMENITIES = {
    'wifi': ('Wi-Fi', 'bi-wifi'),
    'projector': ('Проектор', 'bi-projector'),
    'board': ('Маркерная доска', 'bi-easel2'),
}


class Command(BaseCommand):
    help = 'Заполнить БД тестовыми помещениями'

    def handle(self, *args, **kwargs):
        categories = {
            slug: Category.objects.get_or_create(slug=slug, defaults={'name': name})[0]
            for slug, name in CATEGORIES.items()
        }
        amenities = {
            slug: Amenity.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon},
            )[0]
            for slug, (name, icon) in AMENITIES.items()
        }

        created_count = 0
        for raw_data in SPACES:
            data = raw_data.copy()
            category_slug = data.pop('category')
            amenity_slugs = data.pop('amenities')
            data['category'] = categories[category_slug]
            obj, created = Space.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            obj.amenities.set([amenities[slug] for slug in amenity_slugs])
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Создано: {obj.name}')
            else:
                self.stdout.write(f'  — Уже есть: {obj.name}')
        self.stdout.write(self.style.SUCCESS(f'\nГотово. Создано {created_count} помещений.'))
