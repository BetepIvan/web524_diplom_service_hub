from django.contrib import admin
from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'master_service', 'author', 'created', 'sign_of_review')
    ordering = ('created',)
    list_filter = ('master_service', 'author')
    search_fields = ('title', 'content')