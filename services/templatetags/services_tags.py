from django import template

register = template.Library()


@register.filter()
def service_media(val):
    """Возвращает путь к медиафайлу услуги или заглушку"""
    if val:
        return f'/media/{val}'
    return '/static/dummyservice.jpg'


@register.filter()
def category_media(val):
    """Возвращает путь к медиафайлу категории или заглушку"""
    if val:
        return f'/media/{val}'
    return '/static/dummycategory.jpg'


@register.filter
def class_name(obj):
    """Возвращает имя класса объекта"""
    return obj.__class__.__name__


@register.filter()
def dogs_media(val):
    """Устаревший фильтр, используйте service_media"""
    return service_media(val)
