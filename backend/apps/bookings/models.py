# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class User(AbstractUser):
#     ROLE_CHOICES = [
#         ('guest', 'Гость'),
#         ('client', 'Клиент'),
#         ('manager', 'Менеджер'),
#         ('administrator', 'Администратор'),
#     ]

#     role = models.CharField(
#         max_length=20,
#         choices=ROLE_CHOICES,
#         default='guest',
#         verbose_name='Роль'
#     )

#     class Meta:
#         verbose_name = 'Пользователь'
#         verbose_name_plural = 'Пользователи'

#     def __str__(self):
#         return f"{self.username} ({self.get_role_display()})"

# Амир у тебя 2 одинаковых класса User тут и в models.py в папке users