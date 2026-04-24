from django.urls import path

from users.apps import UsersConfig
from users.views import (
    UserRegisterView, UserLoginView, UserProfileView, UserLogoutView,
    UserUpdateView, UserPasswordChangeView, user_generate_new_password_view,
    UserListView, UserDetailView, BecomeMasterView, MasterProfileCompleteView, MasterDetailView, ProfileManageView
)

app_name = UsersConfig.name

urlpatterns = [
    # работа с аккаунтом
    path('', UserLoginView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('register/', UserRegisterView.as_view(), name='user_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('update/', UserUpdateView.as_view(), name='user_update'),
    path('change_password/', UserPasswordChangeView.as_view(), name='user_change_password'),
    path('profile/change_password/', user_generate_new_password_view, name='user_generate_password'),
    path('profile/manage/', ProfileManageView.as_view(), name='profile_manage'),

    # стать мастером
    path('become-master/', BecomeMasterView.as_view(), name='become_master'),
    path('master-profile/complete/', MasterProfileCompleteView.as_view(), name='master_profile_complete'),
    path('master/<int:pk>/', MasterDetailView.as_view(), name='master_detail'),

    # просмотр других пользователей
    path('all_users/', UserListView.as_view(), name='users_list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
