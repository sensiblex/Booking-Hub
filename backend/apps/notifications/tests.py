from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification
from .services import create_notification


class NotificationModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='notice_user', password='pass')

    def test_create_notification_sets_expected_fields(self):
        notification = create_notification(
            user=self.user,
            notification_type=Notification.TYPE_SPACE_SUBMITTED,
            title='Помещение отправлено',
            message='Заявка принята.',
            url='/spaces/my/',
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.type, Notification.TYPE_SPACE_SUBMITTED)
        self.assertEqual(notification.title, 'Помещение отправлено')
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.url, '/spaces/my/')


class NotificationViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='notice_user', password='pass')
        self.other_user = User.objects.create_user(username='other_user', password='pass')
        self.notification = Notification.objects.create(
            user=self.user,
            type=Notification.TYPE_SPACE_APPROVED,
            title='Одобрено',
            message='Помещение опубликовано.',
        )

    def test_notification_list_requires_auth(self):
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 302)

    def test_user_can_open_list_and_mark_one_read(self):
        self.client.force_login(self.user)
        list_response = self.client.get(reverse('notifications:list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Одобрено')

        read_response = self.client.post(reverse('notifications:mark_read', args=[self.notification.id]))
        self.assertEqual(read_response.status_code, 302)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_user_cannot_mark_foreign_notification_read(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('notifications:mark_read', args=[self.notification.id]))
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read_marks_all_unread_notifications(self):
        Notification.objects.create(
            user=self.user,
            type=Notification.TYPE_BOOKING_REQUEST,
            title='Новая заявка',
            message='У вас новая заявка.',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_profile_renders_bell_and_toast_for_fresh_notifications(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['fresh_notification_ids'] = [self.notification.id]
        session.save()

        response = self.client.get(reverse('users:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bi-bell')
        self.assertContains(response, 'toast-notifications')

    def test_updates_api_returns_new_notifications_and_counter(self):
        Notification.objects.create(
            user=self.user,
            type=Notification.TYPE_BOOKING_REQUEST,
            title='Новая заявка',
            message='Появилась новая заявка.',
            is_read=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('notifications:updates_api'), {'after_id': self.notification.id})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('updates', data)
        self.assertEqual(len(data['updates']), 1)
        self.assertEqual(data['updates'][0]['title'], 'Новая заявка')
        self.assertGreaterEqual(data['unread_count'], 1)

    def test_updates_api_ignores_foreign_user_notifications(self):
        Notification.objects.create(
            user=self.other_user,
            type=Notification.TYPE_BOOKING_REQUEST,
            title='Чужое уведомление',
            message='Не должно прийти.',
            is_read=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('notifications:updates_api'), {'after_id': 0})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(any(item['title'] == 'Чужое уведомление' for item in data['updates']))
