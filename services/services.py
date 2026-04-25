from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from services.models import Category


def get_category_cache():
    if settings.CACHE_ENABLED:
        key = 'category_list'
        category_list = cache.get(key)
        if not category_list:
            category_list = Category.objects.all()
            cache.set(key, category_list)
        else:
            category_list = Category.objects.all()

        return category_list


def send_views_mail(service_object, owner_email, views_count):
    send_mail(
        subject=f'{views_count} просмотров {service_object}',
        message=f'Ура! Уже {views_count} просмотров у услуги "{service_object}"!',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[owner_email, ]
    )
