from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponseRedirect

from services.models import Category, Service, Portfolio, MasterService
from services.forms import CategoryForm, PortfolioForm, MasterServiceForm, ServiceTemplateForm
from users.models import User


def index(request):
    context = {
        'object_list': Category.objects.filter(is_active=True, is_moderated=True, is_main=True)[:6],
        'title': 'Услуги мастеров - Главная',
        'description': 'Добро пожаловать на платформу услуг мастеров!'
    }
    return render(request, 'services/index.html', context)


class CategoryListView(ListView):
    model = Category
    template_name = 'services/categories.html'
    context_object_name = 'categories'
    extra_context = {
        'title': 'Категории услуг',
        'description': 'Выберите категорию услуг'
    }

    def get_queryset(self):
        return Category.objects.filter(is_active=True, is_moderated=True).prefetch_related('service_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем ID категории из GET-параметра
        selected_category_id = self.request.GET.get('category')
        if selected_category_id:
            context['selected_category_id'] = int(selected_category_id)
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'services/category_form.html'
    success_url = reverse_lazy('services:categories_list')
    extra_context = {'title': 'Создать категорию'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.is_moderated = True
        form.instance.is_active = True
        form.instance.is_main = False
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'services/category_form.html'
    success_url = reverse_lazy('services:categories_list')
    extra_context = {'title': 'Редактировать категорию'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderator']:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'services/category_confirm_delete.html'
    success_url = reverse_lazy('services:categories_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderator']:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CategoryModerateView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ('is_moderated', 'is_active')
    template_name = 'services/category_moderate.html'
    success_url = reverse_lazy('services:categories_list')
    extra_context = {'title': 'Модерация категории'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'moderator']:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'moderator':
            if 'is_main' in form.fields:
                del form.fields['is_main']
        return form


class CategorySuggestView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'services/category_suggest.html'
    success_url = reverse_lazy('services:categories_list')
    extra_context = {'title': 'Предложить категорию'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.is_moderated = False
        form.instance.is_active = True
        form.instance.is_main = False
        return super().form_valid(form)


class ServicesByCategoryListView(DetailView):
    model = Category
    template_name = 'services/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()

        # Список всех категорий для левой колонки
        context['categories'] = Category.objects.filter(is_active=True, is_moderated=True)

        # Получаем услуги мастеров в этой категории
        services_list = MasterService.objects.filter(
            service_template__category=category,
            is_active=True
        ).select_related('master', 'service_template', 'service_template__category')

        # Пагинация
        paginator = Paginator(services_list, 10)
        page_number = self.request.GET.get('page')
        context['services'] = paginator.get_page(page_number)
        context['title'] = f'Услуги в категории: {category.name}'

        return context


class AllSearchView(ListView):
    """Поиск мастеров по названию услуги или категории"""
    model = User
    template_name = 'services/all_search_results.html'
    context_object_name = 'results'
    paginate_by = 12
    extra_context = {'title': 'Результаты поиска'}

    def dispatch(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        if not query:
            return redirect('services:index')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        self.search_query = query

        # Поиск категорий по названию
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True,
            is_moderated=True
        )

        # Поиск услуг (шаблонов) по названию
        services = Service.objects.filter(
            title__icontains=query,
            is_template=True
        )

        # Получаем мастеров через найденные услуги
        masters_from_services = User.objects.filter(
            my_services__service_template__in=services,
            my_services__is_active=True,
            role='master'
        ).distinct()

        # Получаем мастеров через найденные категории
        masters_from_categories = User.objects.filter(
            my_services__service_template__category__in=categories,
            my_services__is_active=True,
            role='master'
        ).distinct()

        # Объединяем и возвращаем уникальных мастеров
        return (masters_from_services | masters_from_categories).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.search_query
        return context


class ServiceListView(ListView):
    """Список всех услуг (MasterService)"""
    model = MasterService
    template_name = 'services/services_list.html'
    context_object_name = 'services'
    paginate_by = 9
    extra_context = {
        'title': 'Все услуги',
        'description': 'Услуги от наших мастеров'
    }

    def get_queryset(self):
        return MasterService.objects.filter(is_active=True).select_related('master', 'service_template', 'service_template__category')


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    model = Portfolio
    form_class = PortfolioForm
    template_name = 'services/portfolio_form.html'
    success_url = reverse_lazy('users:user_profile')
    extra_context = {'title': 'Добавить работу в портфолио'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.master = self.request.user
        return super().form_valid(form)


class ServiceLibraryListView(LoginRequiredMixin, ListView):
    """Библиотека услуг - только услуги из категорий мастера"""
    model = Service
    template_name = 'services/service_library.html'
    context_object_name = 'services'
    paginate_by = 12
    extra_context = {
        'title': 'Библиотека услуг',
        'description': 'Выберите услугу, которую хотите добавить в свой профиль'
    }

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        master_categories = self.request.user.categories.all()
        return Service.objects.filter(
            is_template=True,
            category__in=master_categories
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['master_categories'] = self.request.user.categories.all()
        return context


class ServiceTemplateCreateView(LoginRequiredMixin, CreateView):
    """Мастер добавляет новую услугу в библиотеку"""
    model = Service
    form_class = ServiceTemplateForm
    template_name = 'services/service_template_form.html'
    success_url = reverse_lazy('services:service_library')
    extra_context = {'title': 'Добавить новую услугу'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['master'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.is_template = True
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class MasterServiceCreateView(LoginRequiredMixin, CreateView):
    model = MasterService
    form_class = MasterServiceForm
    template_name = 'services/master_service_create.html'
    extra_context = {'title': 'Добавить услугу'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['master'] = self.request.user
        kwargs['selected_service_id'] = self.kwargs.get('pk')
        return kwargs

    def form_valid(self, form):
        # Проверяем, существует ли уже такая услуга у мастера
        existing = MasterService.objects.filter(
            master=self.request.user,
            service_template_id=self.kwargs.get('pk')
        ).first()

        if existing:
            # Если существует, обновляем цену
            existing.price = form.cleaned_data.get('price')
            existing.is_active = True
            existing.save()
            messages.success(self.request, 'Услуга успешно обновлена')
            return redirect(self.get_success_url())

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:master_detail', kwargs={'pk': self.request.user.pk})


class MyServicesListView(LoginRequiredMixin, ListView):
    """Список услуг мастера (добавленные им)"""
    model = MasterService
    template_name = 'services/my_services.html'
    context_object_name = 'my_services'
    paginate_by = 10
    extra_context = {'title': 'Мои услуги'}

    def get_queryset(self):
        return MasterService.objects.filter(master=self.request.user, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_services'] = self.get_queryset().count()
        return context


class MasterServicesListView(ListView):
    """Услуги конкретного мастера"""
    model = MasterService
    template_name = 'services/services_list.html'
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
        return MasterService.objects.filter(master_id=self.kwargs['pk'], is_active=True).select_related('service_template', 'service_template__category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master = get_object_or_404(User, pk=self.kwargs['pk'])
        context['master'] = master
        context['title'] = f'Услуги мастера: {master.get_full_name()}'
        return context


class MasterServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = MasterService
    success_url = reverse_lazy('services:services_list')

    def dispatch(self, request, *args, **kwargs):
        service = self.get_object()
        if service.master != request.user and request.user.role not in ['admin', 'moderator']:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Удаляем без подтверждения
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, 'Услуга успешно удалена')
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class MasterServiceToggleView(LoginRequiredMixin, View):
    """Включить/выключить услугу мастера"""
    def post(self, request, pk):
        service = get_object_or_404(MasterService, pk=pk, master=request.user)
        service.is_active = not service.is_active
        service.save()
        return redirect('users:master_detail', pk=request.user.pk)


def privacy_policy(request):
    """Страница политики конфиденциальности"""
    context = {
        'title': 'Политика конфиденциальности',
        'description': 'Условия обработки и защиты персональных данных на платформе Сервис Мастеров'
    }
    return render(request, 'services/privacy_policy.html', context)
