import base64
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.bookings.models import Booking
from apps.notifications.models import Notification
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

    def test_detail_page_shows_owner_full_name_or_username_fallback(self):
        User = get_user_model()
        owner_with_name = User.objects.create_user(
            username='owner_with_name',
            password='pass',
            first_name='Иван',
            last_name='Иванов',
        )
        owner_without_name = User.objects.create_user(
            username='owner_username_only',
            password='pass',
        )

        space_with_named_owner = Space.objects.create(
            name='Переговорная с именем владельца',
            address='ул. Первая, 1',
            capacity=8,
            price_per_hour=900,
            moderation_status=Space.MODERATION_APPROVED,
            submitted_by=owner_with_name,
        )
        space_with_username_owner = Space.objects.create(
            name='Переговорная с username владельца',
            address='ул. Вторая, 2',
            capacity=8,
            price_per_hour=900,
            moderation_status=Space.MODERATION_APPROVED,
            submitted_by=owner_without_name,
        )
        legacy_space = Space.objects.create(
            name='Legacy помещение без владельца',
            address='ул. Третья, 3',
            capacity=8,
            price_per_hour=900,
            moderation_status=Space.MODERATION_APPROVED,
            submitted_by=None,
        )

        response_with_name = self.client.get(reverse('spaces:detail', args=[space_with_named_owner.pk]))
        self.assertContains(response_with_name, 'Иван Иванов')

        response_with_username = self.client.get(reverse('spaces:detail', args=[space_with_username_owner.pk]))
        self.assertContains(response_with_username, 'owner_username_only')

        response_legacy = self.client.get(reverse('spaces:detail', args=[legacy_space.pk]))
        self.assertContains(response_legacy, 'Владелец не указан')


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
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                type=Notification.TYPE_SPACE_SUBMITTED,
            ).exists()
        )

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

    def test_admin_reject_requires_reason(self):
        space = Space.objects.create(
            name='Площадка для теста причины',
            address='ул. Тест, 1',
            capacity=10,
            price_per_hour=1000,
            moderation_status=Space.MODERATION_PENDING,
        )
        self.client.force_login(self.admin)

        response = self.client.post(reverse('admin_space_moderate', args=[space.pk]), {
            'action': 'reject',
        })

        self.assertRedirects(response, reverse('admin_spaces'))
        space.refresh_from_db()
        self.assertEqual(space.moderation_status, Space.MODERATION_PENDING)

    def test_admin_can_mark_space_as_revision_required_with_reason(self):
        User = get_user_model()
        owner = User.objects.create_user(username='owner_for_revision', password='pass')
        space = Space.objects.create(
            name='Площадка на доработку',
            address='ул. Тест, 5',
            capacity=10,
            price_per_hour=1000,
            moderation_status=Space.MODERATION_PENDING,
            submitted_by=owner,
        )

        response = self.client.post(reverse('admin_space_moderate', args=[space.pk]), {
            'action': 'revision_required',
            'moderation_note': 'Добавьте подробное описание и фото.',
        })

        self.assertRedirects(response, reverse('admin_spaces'))
        space.refresh_from_db()
        self.assertEqual(space.moderation_status, Space.MODERATION_REVISION_REQUIRED)
        self.assertTrue(
            Notification.objects.filter(
                user=owner,
                type=Notification.TYPE_SPACE_REVISION_REQUIRED,
            ).exists()
        )

    def test_admin_revision_required_requires_reason(self):
        space = Space.objects.create(
            name='Площадка без комментария',
            address='ул. Тест, 6',
            capacity=10,
            price_per_hour=1000,
            moderation_status=Space.MODERATION_PENDING,
        )

        response = self.client.post(reverse('admin_space_moderate', args=[space.pk]), {
            'action': 'revision_required',
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


class SpaceOwnerBookingModerationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username='space_owner',
            password='pass',
        )
        self.renter = User.objects.create_user(
            username='renter_user',
            password='pass',
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            password='pass',
        )
        self.space = Space.objects.create(
            name='Помещение владельца',
            address='ул. Владельца, 10',
            capacity=20,
            price_per_hour=1500,
            moderation_status=Space.MODERATION_APPROVED,
            submitted_by=self.owner,
        )

    def _create_booking(self, status):
        return Booking.objects.create(
            user=self.renter,
            space=self.space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
            total_price=3000,
            status=status,
        )

    def test_owner_can_confirm_awaiting_confirmation_booking(self):
        booking = self._create_booking(Booking.STATUS_AWAITING_CONFIRMATION)
        self.client.force_login(self.owner)

        response = self.client.post(reverse('spaces:confirm_booking', args=[booking.pk]))

        self.assertRedirects(response, reverse('spaces:my_spaces'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)

    def test_owner_can_decline_awaiting_confirmation_booking(self):
        booking = self._create_booking(Booking.STATUS_AWAITING_CONFIRMATION)
        self.client.force_login(self.owner)

        response = self.client.post(reverse('spaces:decline_booking', args=[booking.pk]))

        self.assertRedirects(response, reverse('spaces:my_spaces'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)

    def test_non_owner_cannot_change_foreign_booking_status(self):
        booking = self._create_booking(Booking.STATUS_AWAITING_CONFIRMATION)
        self.client.force_login(self.other_user)

        response = self.client.post(reverse('spaces:confirm_booking', args=[booking.pk]))

        self.assertRedirects(response, reverse('spaces:my_spaces'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_AWAITING_CONFIRMATION)

    def test_confirm_or_decline_non_awaiting_booking_is_idempotent(self):
        confirmed_booking = self._create_booking(Booking.STATUS_CONFIRMED)
        cancelled_booking = self._create_booking(Booking.STATUS_CANCELLED)
        self.client.force_login(self.owner)

        self.client.post(reverse('spaces:confirm_booking', args=[confirmed_booking.pk]))
        self.client.post(reverse('spaces:decline_booking', args=[cancelled_booking.pk]))

        confirmed_booking.refresh_from_db()
        cancelled_booking.refresh_from_db()
        self.assertEqual(confirmed_booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(cancelled_booking.status, Booking.STATUS_CANCELLED)

    def test_confirm_and_decline_require_post_method(self):
        booking = self._create_booking(Booking.STATUS_AWAITING_CONFIRMATION)
        self.client.force_login(self.owner)

        response_confirm = self.client.get(reverse('spaces:confirm_booking', args=[booking.pk]))
        response_decline = self.client.get(reverse('spaces:decline_booking', args=[booking.pk]))

        self.assertRedirects(response_confirm, reverse('spaces:my_spaces'))
        self.assertRedirects(response_decline, reverse('spaces:my_spaces'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_AWAITING_CONFIRMATION)


class LandlordBookingManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.landlord = User.objects.create_user(
            username='landlord', password='pass', role='client',
        )
        self.tenant = User.objects.create_user(
            username='tenant', password='pass', role='client',
        )
        self.space = Space.objects.create(
            name='Тестовое помещение',
            address='ул. Тестовая, 1',
            capacity=10,
            price_per_hour=1000,
            submitted_by=self.landlord,
            moderation_status=Space.MODERATION_APPROVED,
        )
        self.booking = Booking.objects.create(
            user=self.tenant,
            space=self.space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
            total_price=2000,
            status=Booking.STATUS_AWAITING_CONFIRMATION,
        )

    def test_my_spaces_shows_landlord_bookings(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse('spaces:my_spaces'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое помещение')
        self.assertContains(response, 'Ожидает подтверждения')

    def test_landlord_can_confirm_booking(self):
        self.client.force_login(self.landlord)
        response = self.client.post(reverse('spaces:confirm_booking', args=[self.booking.id]))
        self.assertRedirects(response, reverse('spaces:my_spaces'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)
        self.assertTrue(
            Notification.objects.filter(
                user=self.tenant,
                type=Notification.TYPE_BOOKING_APPROVED,
            ).exists()
        )

    def test_landlord_can_decline_booking(self):
        self.client.force_login(self.landlord)
        response = self.client.post(reverse('spaces:decline_booking', args=[self.booking.id]))
        self.assertRedirects(response, reverse('spaces:my_spaces'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertTrue(
            Notification.objects.filter(
                user=self.tenant,
                type=Notification.TYPE_BOOKING_DECLINED,
            ).exists()
        )

    def test_tenant_cannot_confirm_booking(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('spaces:confirm_booking', args=[self.booking.id]))
        self.assertRedirects(response, reverse('spaces:my_spaces'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_AWAITING_CONFIRMATION)

    def test_tenant_cannot_decline_booking(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('spaces:decline_booking', args=[self.booking.id]))
        self.assertRedirects(response, reverse('spaces:my_spaces'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_AWAITING_CONFIRMATION)

    def test_unauthenticated_cannot_access_my_spaces(self):
        response = self.client.get(reverse('spaces:my_spaces'))
        self.assertRedirects(response, '/users/login/?next=/spaces/my/')

    def test_landlord_can_edit_rejected_space(self):
        self.space.moderation_status = Space.MODERATION_REJECTED
        self.space.moderation_note = 'Неверный адрес'
        self.space.save()
        self.client.force_login(self.landlord)
        response = self.client.get(reverse('spaces:edit', args=[self.space.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Причина отклонения')
        self.assertContains(response, 'Неверный адрес')

    def test_landlord_cannot_edit_approved_space(self):
        self.space.moderation_status = Space.MODERATION_APPROVED
        self.space.save()
        self.client.force_login(self.landlord)
        response = self.client.get(reverse('spaces:edit', args=[self.space.pk]))
        self.assertRedirects(response, reverse('spaces:my_spaces'))

    def test_edit_rejected_space_resubmits_for_moderation(self):
        self.space.moderation_status = Space.MODERATION_REJECTED
        self.space.moderation_note = 'Неверный адрес'
        self.space.save()
        self.client.force_login(self.landlord)
        response = self.client.post(reverse('spaces:edit', args=[self.space.pk]), {
            'name': 'Новое название',
            'address': 'ул. Исправленная, 5',
            'capacity': '15',
            'price_per_hour': '1200',
        })
        self.assertRedirects(response, reverse('spaces:my_spaces'))
        self.space.refresh_from_db()
        self.assertEqual(self.space.moderation_status, Space.MODERATION_PENDING)
        self.assertEqual(self.space.moderation_note, '')
        self.assertEqual(self.space.name, 'Новое название')
        self.assertTrue(
            Notification.objects.filter(
                user=self.landlord,
                type=Notification.TYPE_SPACE_RESUBMITTED,
            ).exists()
        )

    def test_my_spaces_shows_revision_required_note(self):
        self.space.moderation_status = Space.MODERATION_REVISION_REQUIRED
        self.space.moderation_note = 'Добавьте фото и описание.'
        self.space.save()
        self.client.force_login(self.landlord)

        response = self.client.get(reverse('spaces:my_spaces'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'На доработку')
        self.assertContains(response, 'Добавьте фото и описание.')

    def test_other_user_cannot_edit_space(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('spaces:edit', args=[self.space.pk]))
        self.assertEqual(response.status_code, 404)
