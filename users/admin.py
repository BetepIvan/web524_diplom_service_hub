from django.contrib import admin
from users.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Что отображаем в списке
    list_display = ('id', 'email', 'last_name', 'first_name', 'role', 'is_active')

    # Что можно редактировать прямо в списке
    list_editable = ('role', 'is_active')

    # По каким полям фильтруем (боковая панель)
    list_filter = ('role', 'is_active')

    # По каким полям ищем (сверху появится строка поиска)
    search_fields = ('email', 'last_name', 'first_name', 'phone')
