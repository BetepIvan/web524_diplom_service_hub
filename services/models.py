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
    """Услуга - шаблон (библиотека)"""
    title = models.CharField(max_length=250, verbose_name='Название услуги')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание услуги', **NULLABLE)
    is_template = models.BooleanField(default=True, verbose_name='Шаблон услуги')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, **NULLABLE, verbose_name='Создал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.title

    @property
    def specialists_count(self):
        """Количество мастеров, оказывающих эту услугу"""
        return self.master_services.filter(is_active=True).count()

    class Meta:
        verbose_name = 'услуга (шаблон)'
        verbose_name_plural = 'услуги (библиотека)'
        ordering = ['title']


class MasterService(models.Model):
    """Услуга мастера - конкретная цена от конкретного мастера"""
    master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_services',
        verbose_name='Мастер'
    )
    service_template = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='master_services',
        verbose_name='Услуга'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, **NULLABLE, verbose_name='Цена (₽)')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    def __str__(self):
        return f'{self.service_template.title} - {self.master.email}'

    class Meta:
        verbose_name = 'услуга мастера'
        verbose_name_plural = 'услуги мастеров'
        ordering = ['-created_at']
        unique_together = ['master', 'service_template']


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

class Portfolio(models.Model):
    """Портфолио мастера - примеры выполненных работ"""
    master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio_items',
        verbose_name='Мастер'
    )
    title = models.CharField(max_length=200, verbose_name='Название работы')
    description = models.TextField(verbose_name='Описание', **NULLABLE)
    image = models.ImageField(upload_to='portfolio/', verbose_name='Фото')
    price = models.DecimalField(max_digits=10, decimal_places=2, **NULLABLE, verbose_name='Цена работы')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Портфолио'
        verbose_name_plural = 'Портфолио'
        ordering = ['-created_at']