import random
import string

from django.shortcuts import reverse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from users.models import User
from users.forms import UserRegisterForm, UserLoginForm, UserUpdateForm, UserChangePasswordForm, UserForm
from users.services import send_register_email, send_new_password


class UserRegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy('users:user_login')
    template_name = 'users/user_register_update.html'
    extra_context = {
        'title': 'Создать аккаунт',
    }

    def form_valid(self, form):
        self.object = form.save()
        send_register_email(self.object.email)
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'users/user_login.html'
    form_class = UserLoginForm
    extra_context = {
        'title': 'Авторизация'
    }


class UserProfileView(DetailView):
    model = User
    form_class = UserForm
    template_name = 'users/user_profile_read_only.html'
    extra_context = {
        'hide_jumbotron': True
    }

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        user_obj = self.get_object()
        context_data['title'] = f'Профиль пользователя {user_obj}'
        return context_data


class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/user_register_update.html'
    success_url = reverse_lazy('users:user_profile')
    extra_context = {
        'hide_jumbotron': True
    }

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        user_obj = self.get_object()
        context_data['title'] = f'Изменить профиль: {user_obj}'
        return context_data


class UserPasswordChangeView(PasswordChangeView):
    form_class = UserChangePasswordForm  # было from_class (опечатка)
    template_name = 'users/user_change_password.html'
    success_url = reverse_lazy('users:user_profile')
    extra_context = {
        'hide_jumbotron': True
    }

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        user_obj = self.get_object()
        context_data['title'] = f'Изменить пароль: {user_obj}'
        return context_data


class UserLogoutView(LogoutView):
    template_name = 'users/user_logout.html'
    extra_context = {
        'title': 'Выход из аккаунта'
    }


class UserListView(LoginRequiredMixin, ListView):
    model = User
    extra_context = {
        'title': 'Все наши пользователи'
    }
    template_name = 'users/users.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


class UserDetailView(DetailView):
    model = User
    template_name = 'users/user_detail.html'
    extra_context = {
        'hide_jumbotron': True
    }

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        user_object = self.get_object()
        context_data['title'] = f'Профиль пользователя {user_object}'
        return context_data


@login_required(login_url='users:user_login')
def user_generate_new_password_view(request):
    new_password = ''.join(random.sample(string.ascii_letters + string.digits, k=12))
    request.user.set_password(new_password)
    request.user.save()
    send_new_password(request.user.email, new_password)
    return redirect(reverse('services:index'))
