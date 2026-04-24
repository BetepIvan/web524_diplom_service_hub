import random
import string

from django.core.exceptions import PermissionDenied
from django.shortcuts import reverse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from users.models import User
from users.forms import (
    UserRegisterForm, UserLoginForm, UserUpdateForm, UserChangePasswordForm,
    UserForm, BecomeMasterForm, MasterProfileForm
)
from users.services import send_register_email, send_new_password
from services.models import Service
from reviews.models import Review


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
    form_class = UserChangePasswordForm
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
    template_name = 'users/users.html'
    paginate_by = 6

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(is_active=True)

        # Мастера и клиенты видят только мастеров
        if user.role in ['master', 'user']:
            queryset = queryset.filter(role='master')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role in ['master', 'user']:
            context['title'] = 'Мастера'
            context['description'] = 'Выберите мастера для вашей задачи'
        else:
            context['title'] = 'Управление пользователями'
            context['description'] = 'Полный список пользователей системы'

        return context


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


class MasterDetailView(DetailView):
    model = User
    template_name = 'users/master_detail.html'
    context_object_name = 'master'

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['pk'], role='master')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master = self.get_object()
        context['services'] = Service.objects.filter(owner=master, is_active=True)
        context['reviews'] = Review.objects.filter(service__owner=master, sign_of_review=True)[:10]
        context['title'] = f'Мастер: {master.get_full_name()}'
        context['hide_jumbotron'] = True
        return context


class BecomeMasterView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = BecomeMasterForm
    template_name = 'users/become_master_form.html'
    success_url = reverse_lazy('users:master_profile_complete')
    extra_context = {'title': 'Стать мастером'}

    def get_object(self, queryset=None):
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'user':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'master'
        user.save()
        form.save_m2m()
        return super().form_valid(form)


class MasterProfileCompleteView(LoginRequiredMixin, TemplateView):
    template_name = 'users/master_profile_complete.html'
    extra_context = {'title': 'Профиль мастера заполнен'}


class ProfileManageView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm  # Добавляем form_class
    template_name = 'users/profile_manage.html'
    success_url = reverse_lazy('users:user_profile')
    extra_context = {'title': 'Управление профилем'}

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == 'POST':
            context['user_form'] = UserUpdateForm(self.request.POST, self.request.FILES, instance=self.request.user)
            if self.request.user.role == 'master':
                context['master_form'] = MasterProfileForm(self.request.POST, self.request.FILES,
                                                           instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
            if self.request.user.role == 'master':
                context['master_form'] = MasterProfileForm(instance=self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)

        if request.user.role == 'master':
            master_form = MasterProfileForm(request.POST, request.FILES, instance=request.user)
            if user_form.is_valid() and master_form.is_valid():
                user_form.save()
                master_form.save()
                return redirect(self.success_url)
        else:
            if user_form.is_valid():
                user_form.save()
                return redirect(self.success_url)

        return self.render_to_response(self.get_context_data())


@login_required(login_url='users:user_login')
def user_generate_new_password_view(request):
    new_password = ''.join(random.sample(string.ascii_letters + string.digits, k=12))
    request.user.set_password(new_password)
    request.user.save()
    send_new_password(request.user.email, new_password)
    return redirect(reverse('services:index'))