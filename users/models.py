from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

NULLABLE = {'blank': True, 'null': True}


class UserRoles(models.TextChoices):
    ADMIN = 'admin', _('admin')
    MODERATOR = 'moderator', _('moderator')
    MASTER = 'master', _('master')
    USER = 'user', _('user')


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Электронная почта')
    role = models.CharField(max_length=9, choices=UserRoles.choices, default=UserRoles.USER)
    first_name = models.CharField(max_length=150, verbose_name='Имя', default='Anonymous')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия', default='Anonymous')
    location = models.CharField(max_length=200, verbose_name='Город/Адрес', **NULLABLE)
    avatar = models.ImageField(upload_to='users/', verbose_name='Аватар', **NULLABLE)
    phone = models.CharField(max_length=35, verbose_name='Номер телефона', **NULLABLE)
    work_days = models.CharField(max_length=200, default='Пн-Сб: 09:00-18:00, Вс: выходной', verbose_name='График работы', **NULLABLE)
    telegram = models.CharField(max_length=150, verbose_name='Аккаунт телеграм', **NULLABLE)
    max_messenger = models.CharField(max_length=150, verbose_name='Аккаунт МАХ', **NULLABLE)
    is_active = models.BooleanField(default=True, verbose_name='Состояние аккаунта')

    # Поля для профиля мастера
    categories = models.ManyToManyField('services.Category', blank=True, verbose_name='Категории услуг')
    experience = models.IntegerField(default=0, verbose_name='Опыт (лет)', **NULLABLE)
    education = models.CharField(max_length=500, verbose_name='Образование', **NULLABLE)
    about = models.TextField(verbose_name='О себе', **NULLABLE)
    service_description = models.TextField(verbose_name='Описание деятельности', **NULLABLE)
    portfolio = models.ImageField(upload_to='portfolio/', **NULLABLE, verbose_name='Портфолио')
    is_master_approved = models.BooleanField(default=False, verbose_name='Профиль мастера подтверждён')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @property
    def has_master_profile(self):
        """Проверяет, заполнен ли профиль мастера"""
        return self.role == 'master'

    def __str__(self):
        return f'{self.email}\n{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['id']