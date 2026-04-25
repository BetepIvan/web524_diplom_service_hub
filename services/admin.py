from django.contrib import admin
from services.models import Category, Service, Portfolio, MasterService


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_main', 'is_moderated', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_main', 'is_moderated', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_main', 'is_moderated', 'is_active')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'category', 'is_template', 'created_by')
    list_filter = ('category', 'is_template')
    search_fields = ('title',)
    ordering = ('title',)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'master', 'price', 'created_at')
    list_filter = ('master',)
    search_fields = ('title', 'description')


@admin.register(MasterService)
class MasterServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_template', 'master', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'master')
    search_fields = ('service_template__title', 'master__email')
    list_editable = ('price', 'is_active')