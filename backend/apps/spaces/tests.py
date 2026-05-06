import base64

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Amenity, Category, Space, SpacePhoto
from .utils import filter_spaces


PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='
)


def uploaded_png(name):
    return SimpleUploadedFile(name, PNG_BYTES, content_type='image/png')


class SpaceCatalogModelTests(TestCase):
    def test_space_can_have_category_and_amenities(self):
        category, _ = Category.objects.get_or_create(
            slug='meeting-room',
            defaults={'name': 'Переговорная'},
        )
        projector, _ = Amenity.objects.get_or_create(
            slug='projector',
            defaults={'name': 'Проектор'},
        )

        space = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
            category=category,
        )
        space.amenities.add(projector)

        self.assertEqual(str(category), 'Переговорная')
        self.assertEqual(str(projector), 'Проектор')
        self.assertEqual(space.category, category)
        self.assertQuerySetEqual(space.amenities.all(), [projector])


class SpacePhotoModelTests(TestCase):
    def test_space_can_have_multiple_photos(self):
        space = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
        )

        first = SpacePhoto.objects.create(
            space=space,
            image=uploaded_png('first.png'),
            alt_text='Первый ракурс',
            sort_order=2,
        )
        second = SpacePhoto.objects.create(
            space=space,
            image=uploaded_png('second.png'),
            alt_text='Второй ракурс',
            sort_order=1,
        )

        self.assertQuerySetEqual(space.photos.all(), [second, first])


class SpaceCatalogFilterTests(TestCase):
    def setUp(self):
        self.meeting, _ = Category.objects.get_or_create(
            slug='meeting-room',
            defaults={'name': 'Переговорная'},
        )
        self.loft, _ = Category.objects.get_or_create(
            slug='loft',
            defaults={'name': 'Лофт'},
        )
        self.projector, _ = Amenity.objects.get_or_create(
            slug='projector',
            defaults={'name': 'Проектор'},
        )
        self.wifi, _ = Amenity.objects.get_or_create(
            slug='wifi',
            defaults={'name': 'Wi-Fi'},
        )

        self.newton = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
            category=self.meeting,
            moderation_status=Space.MODERATION_APPROVED,
        )
        self.newton.amenities.add(self.wifi)

        self.loft_space = Space.objects.create(
            name='Открытое пространство Лофт',
            address='пр. Победы, 88',
            capacity=50,
            price_per_hour=3800,
            category=self.loft,
            moderation_status=Space.MODERATION_APPROVED,
        )
        self.loft_space.amenities.add(self.projector, self.wifi)

    def test_filter_spaces_applies_query_category_capacity_price_and_amenities(self):
        filtered = filter_spaces(
            Space.objects.all(),
            {
                'q': 'Лофт',
                'category': 'loft',
                'capacity_min': '20',
                'price_max': '4000',
                'amenities': ['projector', 'wifi'],
            },
        )

        self.assertQuerySetEqual(filtered, [self.loft_space])

    def test_space_list_view_uses_backend_filters(self):
        response = self.client.get(reverse('spaces:list'), {
            'category': 'meeting-room',
            'amenities': ['wifi'],
            'capacity_max': '10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Переговорная Ньютон')
        self.assertNotContains(response, 'Открытое пространство Лофт')

    def test_space_list_has_submit_button(self):
        response = self.client.get(reverse('spaces:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добавить помещение')
        self.assertContains(response, reverse('spaces:submit'))


class SpaceDetailCarouselTests(TestCase):
    def test_detail_page_loads_carousel_script_and_marks_gallery(self):
        category, _ = Category.objects.get_or_create(
            slug='meeting-room',
            defaults={'name': 'Переговорная'},
        )
        space = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
            category=category,
            moderation_status=Space.MODERATION_APPROVED,
        )

        response = self.client.get(reverse('spaces:detail', args=[space.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-carousel')
        self.assertContains(response, 'js/carousel.js')

    def test_detail_page_renders_multiple_space_photos_as_carousel_slides(self):
        space = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
            moderation_status=Space.MODERATION_APPROVED,
        )
        SpacePhoto.objects.create(space=space, image=uploaded_png('first.png'), alt_text='Первый ракурс')
        SpacePhoto.objects.create(space=space, image=uploaded_png('second.png'), alt_text='Второй ракурс')

        response = self.client.get(reverse('spaces:detail', args=[space.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-carousel-slide', count=2)
        self.assertContains(response, 'Первый ракурс')
        self.assertContains(response, 'Второй ракурс')


class AdminSpacePhotoUploadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username='admin',
            password='pass',
            is_staff=True,
            role='administrator',
        )
        self.client.force_login(self.admin)

    def test_admin_space_create_form_has_multiple_photo_slots(self):
        response = self.client.get(reverse('admin_space_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="file" name="photos"', count=3)
        self.assertContains(response, 'data-photo-input')
        self.assertContains(response, 'data-add-photo')

    def test_admin_space_create_accepts_multiple_photos(self):
        response = self.client.post(reverse('admin_space_create'), {
            'name': 'Переговорная Ньютон',
            'address': 'ул. Пушкина, 5',
            'capacity': '8',
            'price_per_hour': '900',
            'description': 'Описание',
            'photos': [uploaded_png('first.png'), uploaded_png('second.png')],
            'has_wifi': 'on',
        })

        self.assertRedirects(response, reverse('admin_spaces'))
        space = Space.objects.get(name='Переговорная Ньютон')
        self.assertEqual(space.photos.count(), 2)


class UserSpaceSubmissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='client',
            password='pass',
            role='client',
        )

    def test_client_can_submit_space_for_moderation(self):
        self.client.force_login(self.user)
        wifi, _ = Amenity.objects.get_or_create(slug='wifi', defaults={'name': 'Wi-Fi'})
        projector, _ = Amenity.objects.get_or_create(slug='projector', defaults={'name': 'Проектор'})

        response = self.client.post(reverse('spaces:submit'), {
            'name': 'Зал для лекций',
            'address': 'ул. Тестовая, 1',
            'capacity': '30',
            'price_per_hour': '2500',
            'description': 'Новый зал',
            'amenities': [wifi.pk, projector.pk],
        })

        self.assertRedirects(response, reverse('users:profile'))
        space = Space.objects.get(name='Зал для лекций')
        self.assertEqual(space.submitted_by, self.user)
        self.assertEqual(space.moderation_status, Space.MODERATION_PENDING)
        self.assertTrue(space.has_wifi)
        self.assertTrue(space.has_projector)

    def test_submit_form_does_not_duplicate_amenity_fields(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('spaces:submit'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="has_wifi"')
        self.assertNotContains(response, 'name="has_projector"')
        self.assertNotContains(response, 'name="has_board"')

    def test_pending_space_is_hidden_from_public_catalog_and_detail(self):
        pending_space = Space.objects.create(
            name='Черновик площадки',
            address='ул. Скрытая, 10',
            capacity=15,
            price_per_hour=1200,
            moderation_status=Space.MODERATION_PENDING,
        )
        approved_space = Space.objects.create(
            name='Опубликованная площадка',
            address='ул. Открытая, 1',
            capacity=10,
            price_per_hour=900,
            moderation_status=Space.MODERATION_APPROVED,
        )

        list_response = self.client.get(reverse('spaces:list'))
        self.assertContains(list_response, approved_space.name)
        self.assertNotContains(list_response, pending_space.name)

        detail_response = self.client.get(reverse('spaces:detail', args=[pending_space.pk]))
        self.assertEqual(detail_response.status_code, 404)


class SpaceModerationAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username='moderator',
            password='pass',
            is_staff=True,
            role='administrator',
        )
        self.client.force_login(self.admin)

    def test_admin_can_approve_space_submission(self):
        space = Space.objects.create(
            name='Площадка на проверке',
            address='ул. Пример, 7',
            capacity=12,
            price_per_hour=1400,
            moderation_status=Space.MODERATION_PENDING,
        )

        response = self.client.post(reverse('admin_space_moderate', args=[space.pk]), {
            'action': 'approve',
            'moderation_note': 'Проверено',
        })

        self.assertRedirects(response, reverse('admin_spaces'))
        space.refresh_from_db()
        self.assertEqual(space.moderation_status, Space.MODERATION_APPROVED)
        self.assertEqual(space.moderation_note, 'Проверено')

    def test_admin_can_return_space_to_pending(self):
        space = Space.objects.create(
            name='Одобренная площадка',
            address='ул. Пример, 9',
            capacity=20,
            price_per_hour=2000,
            moderation_status=Space.MODERATION_APPROVED,
        )

        response = self.client.post(reverse('admin_space_moderate', args=[space.pk]), {
            'action': 'pending',
        })

        self.assertRedirects(response, reverse('admin_spaces'))
        space.refresh_from_db()
        self.assertEqual(space.moderation_status, Space.MODERATION_PENDING)


class SeedSpacesCommandTests(TestCase):
    def test_seed_spaces_creates_pending_and_approved_data(self):
        call_command('seed_spaces')

        self.assertGreater(Space.objects.filter(moderation_status=Space.MODERATION_APPROVED).count(), 0)
        self.assertGreater(Space.objects.filter(moderation_status=Space.MODERATION_PENDING).count(), 0)
        self.assertTrue(
            Space.objects.filter(
                moderation_status=Space.MODERATION_PENDING,
                submitted_by__username='applicant_one',
            ).exists()
        )
