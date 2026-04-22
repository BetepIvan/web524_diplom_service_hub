from django.contrib import admin

from services.models import Category, Service


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name',)
    ordering = ('pk',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'category', 'owner')
    list_filter = ('category',)
    ordering = ('title',)
