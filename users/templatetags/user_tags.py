from django import template

register = template.Library()


@register.filter()
def user_media(val):
    if val:
        return fr'/media/{val}'
    return '/static/noavatar.png'

@register.filter
def average_rating(reviews):
    if not reviews:
        return 0
    total = sum(review.rating for review in reviews)
    return round(total / len(reviews), 1)
