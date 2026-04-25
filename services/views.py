from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import inlineformset_factory
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponseRedirect

from services.models import Category, Service, ServiceImage, Portfolio, MasterService
from services.forms import ServiceForm, ServiceCreateForm, ServiceAdminForm, ServiceImageForm, CategoryForm, \
    PortfolioForm, MasterServiceForm, ServiceTemplateForm
from services.services import send_views_mail
from users.services import send_service_creation
from users.models import UserRoles, User


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


class ServiceByMasterListView(ListView):
    model = Service
    template_name = 'services/services.html'
    context_object_name = 'object_list'
    paginate_by = 6
    extra_context = {'title': 'Услуги мастера'}

    def get_queryset(self):
        return Service.objects.filter(owner_id=self.kwargs['pk'], is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master = get_object_or_404(User, pk=self.kwargs['pk'])
        context['master'] = master
        context['title'] = f'Услуги мастера: {master.get_full_name()}'
        return context


class CategorySearchListView(ListView):
    model = Category
    template_name = 'services/categories.html'
    extra_context = {'title': 'Результаты поиска категорий'}

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Category.objects.filter(Q(name__icontains=query))


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
            Q(name__icontains=query) &
            Q(is_active=True) &
            Q(is_moderated=True)
        )

        # Поиск услуг (шаблонов) по названию
        services = Service.objects.filter(
            Q(title__icontains=query) &
            Q(is_template=True)
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


class ServiceDeactivatedListView(LoginRequiredMixin, ListView):
    model = Service
    extra_context = {'title': 'Неактивные услуги'}
    template_name = 'services/services.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role in [UserRoles.MODERATOR, UserRoles.ADMIN]:
            queryset = queryset.filter(is_active=False)
        if self.request.user.role == UserRoles.USER:
            queryset = queryset.filter(is_active=False, owner=self.request.user)
        return queryset


class ServiceSearchListView(ListView):
    model = Service
    template_name = 'services/services.html'
    extra_context = {'title': 'Результаты поиска услуг'}

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Service.objects.filter(Q(title__icontains=query), is_active=True)


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


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceCreateForm
    template_name = 'services/create_update.html'
    extra_context = {'title': 'Добавить услугу'}
    success_url = reverse_lazy('services:services_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'master':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['master'] = self.request.user
        return kwargs

    def form_valid(self, form):
        service_object = form.save(commit=False)
        service_object.owner = self.request.user
        service_object.save()
        send_service_creation(self.request.user.email, service_object)
        return super().form_valid(form)


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'services/detail.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        service_object = self.get_object()
        context_data['title'] = f'Подробная информация\n{service_object}'
        service_object_increase = get_object_or_404(Service, pk=service_object.pk)
        if service_object.owner != self.request.user and not self.request.user.is_staff:
            service_object_increase.views_count()
        if service_object.owner:
            object_owner_email = service_object.owner.email
            if service_object_increase.views % 20 == 0 and service_object_increase.views != 0:
                send_views_mail(service_object, object_owner_email, service_object_increase.views)
        return context_data


class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    template_name = 'services/create_update.html'

    def get_form_class(self):
        service_forms = {
            'admin': ServiceAdminForm,
            'moderator': ServiceForm,
            'user': ServiceForm,
        }
        return service_forms.get(self.request.user.role, ServiceForm)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        ServiceImageFormset = inlineformset_factory(Service, ServiceImage, form=ServiceImageForm, extra=1)
        if self.request.method == 'POST':
            formset = ServiceImageFormset(self.request.POST, self.request.FILES, instance=self.object)
        else:
            formset = ServiceImageFormset(instance=self.object)
        context_data['formset'] = formset
        context_data['title'] = f'Изменить\n{self.get_object()}'
        return context_data

    def form_valid(self, form):
        context_data = self.get_context_data()
        formset = context_data['formset']
        service_object = form.save()
        if formset.is_valid():
            formset.instance = service_object
            formset.save()
        return super().form_valid(form)

    def get_object(self, queryset=None):
        service_object = super().get_object(queryset)
        if service_object.owner != self.request.user:
            raise PermissionDenied
        return service_object

    def get_success_url(self):
        return reverse('services:service_detail', args=[self.kwargs.get('pk')])


class ServiceDeleteView(PermissionRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/delete.html'
    success_url = reverse_lazy('services:services_list')
    permission_required = 'services.delete_service'
    permission_denied_message = 'У вас нет необходимых прав для этого действия'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data['title'] = f'Удалить\n{self.get_object()}'
        return context_data


def service_toggle_activity(request, pk):
    service_object = get_object_or_404(Service, pk=pk)
    service_object.is_active = not service_object.is_active
    service_object.save()
    return redirect(reverse('services:services_list'))


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
