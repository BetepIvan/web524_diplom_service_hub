from django.db import models
from django.conf import settings

from users.models import NULLABLE


class Category(models.Model):
    """Категория услуг (сантехник, электрик, ремонт и т.д.)"""
    name = models.CharField(max_length=100, verbose_name='Категория')
    description = models.CharField(max_length=1000, verbose_name='Описание', **NULLABLE)
    icon = models.CharField(max_length=50, default='fas fa-image', verbose_name='Иконка')
    image = models.ImageField(upload_to='categories/', **NULLABLE, verbose_name='Изображение')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    is_moderated = models.BooleanField(default=False, verbose_name='Прошла модерацию')
    is_main = models.BooleanField(default=False, verbose_name='Показывать на главной')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **NULLABLE,
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']


class Service(models.Model):
    """Услуга, которую предлагает мастер"""

    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Завершена'
        ARCHIVED = 'archived', 'Архивирована'

    title = models.CharField(max_length=250, verbose_name='Название услуги')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание услуги', **NULLABLE)
    photo = models.ImageField(upload_to='services/', **NULLABLE, verbose_name='Фотография')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена (₽)', **NULLABLE)
    location = models.CharField(max_length=200, verbose_name='Город/Адрес', **NULLABLE)

    is_active = models.BooleanField(default=True, verbose_name='Активность объявления')
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name='Статус'
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **NULLABLE,
        verbose_name='Мастер'
    )
    views = models.IntegerField(default=0, verbose_name='Просмотры')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'{self.title} ({self.category})'

    def views_count(self):
        self.views += 1
        self.save()

    class Meta:
        verbose_name = 'услуга'
        verbose_name_plural = 'услуги'
        ordering = ['-created_at']


# Модель DogParent удаляем, либо переделываем в ServiceImage
class ServiceImage(models.Model):
    """Дополнительные фото для услуги"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images', verbose_name='Услуга')
    image = models.ImageField(upload_to='services/gallery/', verbose_name='Фото')
    is_main = models.BooleanField(default=False, verbose_name='Основное фото')

    def __str__(self):
        return f'Фото для {self.service.title}'

    class Meta:
        verbose_name = 'фото услуги'
        verbose_name_plural = 'фото услуг'