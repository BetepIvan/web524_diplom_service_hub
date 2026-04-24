from django.contrib import admin

from services.models import Category, Service, Portfolio


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_main', 'is_moderated', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_main', 'is_moderated', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_main', 'is_moderated', 'is_active')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'category', 'owner')
    list_filter = ('category',)
    ordering = ('title',)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'master', 'price', 'created_at')
    list_filter = ('master',)
    search_fields = ('title', 'description')
