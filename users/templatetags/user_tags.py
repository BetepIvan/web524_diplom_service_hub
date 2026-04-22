from django import template

register = template.Library()


@register.filter()
def user_media(val):
    if val:
        return fr'/media/{val}'
    return '/static/noavatar.png'
