from datetime import timedelta

import factory
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.User'
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user_{n}')
    password = factory.PostGenerationMethodCall('set_password', 'pass')
    role = 'client'


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'spaces.Category'
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')


class SpaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'spaces.Space'

    name = factory.Sequence(lambda n: f'Space {n}')
    address = 'ул. Тестовая, 1'
    capacity = 10
    price_per_hour = 1000
    moderation_status = 'approved'


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'bookings.Booking'

    user = factory.SubFactory(UserFactory)
    space = factory.SubFactory(SpaceFactory)
    check_in = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    check_out = factory.LazyAttribute(lambda o: o.check_in + timedelta(hours=2))
    total_price = 2000
    status = 'pending'
