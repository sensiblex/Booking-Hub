from django.db import migrations, models
import django.db.models.deletion


CATEGORIES = (
    ('meeting-room', 'Переговорная'),
    ('conference-hall', 'Конференц-зал'),
    ('loft', 'Лофт / Open space'),
    ('office', 'Кабинет'),
    ('training-room', 'Учебный класс'),
    ('event-hall', 'Подиум / Зал'),
)

AMENITIES = (
    ('wifi', 'Wi-Fi', 'bi-wifi'),
    ('projector', 'Проектор', 'bi-projector'),
    ('board', 'Маркерная доска', 'bi-easel2'),
)


def seed_catalog_data(apps, schema_editor):
    Category = apps.get_model('spaces', 'Category')
    Amenity = apps.get_model('spaces', 'Amenity')
    Space = apps.get_model('spaces', 'Space')

    categories = {
        slug: Category.objects.get_or_create(slug=slug, defaults={'name': name})[0]
        for slug, name in CATEGORIES
    }
    amenities = {
        slug: Amenity.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'icon': icon},
        )[0]
        for slug, name, icon in AMENITIES
    }

    category_keywords = (
        ('conference-hall', ('конференц',)),
        ('meeting-room', ('переговор',)),
        ('loft', ('лофт', 'open')),
        ('office', ('кабинет',)),
        ('training-room', ('тренинг', 'учеб')),
        ('event-hall', ('подиум', 'зал')),
    )

    for space in Space.objects.all():
        lowered_name = space.name.lower()
        for slug, keywords in category_keywords:
            if any(keyword in lowered_name for keyword in keywords):
                space.category = categories[slug]
                break

        space.save(update_fields=['category'])

        if space.has_wifi:
            space.amenities.add(amenities['wifi'])
        if space.has_projector:
            space.amenities.add(amenities['projector'])
        if space.has_board:
            space.amenities.add(amenities['board'])


def unseed_catalog_data(apps, schema_editor):
    Category = apps.get_model('spaces', 'Category')
    Amenity = apps.get_model('spaces', 'Amenity')
    Category.objects.filter(slug__in=[slug for slug, _name in CATEGORIES]).delete()
    Amenity.objects.filter(slug__in=[slug for slug, _name, _icon in AMENITIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('spaces', '0002_alter_space_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(max_length=140, unique=True, verbose_name='Слаг')),
                ('icon', models.CharField(blank=True, max_length=60, verbose_name='Bootstrap icon')),
            ],
            options={
                'verbose_name': 'Удобство',
                'verbose_name_plural': 'Удобства',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(max_length=140, unique=True, verbose_name='Слаг')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='space',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spaces', to='spaces.category', verbose_name='Категория'),
        ),
        migrations.AddField(
            model_name='space',
            name='amenities',
            field=models.ManyToManyField(blank=True, related_name='spaces', to='spaces.amenity', verbose_name='Удобства'),
        ),
        migrations.RunPython(seed_catalog_data, unseed_catalog_data),
    ]
