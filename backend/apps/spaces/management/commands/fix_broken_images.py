import os
from django.core.management.base import BaseCommand
from apps.spaces.models import Space


class Command(BaseCommand):
    help = 'Очищает поле image у помещений, где файл не существует на диске'

    def handle(self, *args, **kwargs):
        fixed = 0
        for space in Space.objects.exclude(image=''):
            if not space.image:
                continue
            try:
                path = space.image.path
            except Exception:
                path = None

            if not path or not os.path.isfile(path):
                self.stdout.write(
                    f'  ✗ Битая ссылка: {space.name} → {space.image.name}'
                )
                space.image = None
                space.save(update_fields=['image'])
                fixed += 1

        if fixed:
            self.stdout.write(
                self.style.SUCCESS(f'\nГотово. Исправлено записей: {fixed}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nВсё чисто — битых ссылок не найдено.')
            )
