from django.core.management import BaseCommand
from users.models import User, UserRoles  # Уже есть, хорошо


class Command(BaseCommand):
    def handle(self, *args, **options):
        users_data = [
            {
                'email': 'admin@web.top',
                'role': UserRoles.ADMIN,
                'first_name': 'Admin',
                'last_name': 'Adminov',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'moderator@web.top',
                'role': UserRoles.MODERATOR,
                'first_name': 'Moder',
                'last_name': 'Moderov',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'email': 'master@web.top',
                'role': UserRoles.MASTER,  # Теперь эта роль существует
                'first_name': 'Ivan',
                'last_name': 'Masterov',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'client@web.top',  # Добавить обычного клиента
                'role': UserRoles.USER,
                'first_name': 'Petr',
                'last_name': 'Clientov',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for item in users_data:
            user, created = User.objects.update_or_create(
                email=item['email'],
                defaults={
                    'role': item['role'],
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'is_staff': item['is_staff'],
                    'is_superuser': item['is_superuser'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('qwert24')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.email} ({user.role})'))
            else:
                self.stdout.write(self.style.WARNING(f'Пользователь {user.email} уже существует'))
