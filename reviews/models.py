from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import NULLABLE


class Review(models.Model):
    title = models.CharField(max_length=150, verbose_name='Заголовок')
    slug = models.SlugField(max_length=25, unique=True, db_index=True, verbose_name='URL')
    content = models.TextField(verbose_name='Содержимое')
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка'
    )
    created = models.DateTimeField(verbose_name='Создан', auto_now_add=True)
    sign_of_review = models.BooleanField(default=False, verbose_name='Активность')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, **NULLABLE, verbose_name='Автор', related_name='reviews')
    master = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='master_reviews', verbose_name='Мастер', **NULLABLE)

    def __str__(self):
        return f'{self.title} - {self.rating}★'

    def get_absolute_url(self):
        return reverse('reviews:review_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['author', 'master']  # Один пользователь - один отзыв на мастера
