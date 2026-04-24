from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import inlineformset_factory
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator

from services.models import Category, Service, ServiceImage, Portfolio
from services.forms import ServiceForm, ServiceCreateForm, ServiceAdminForm, ServiceImageForm, CategoryForm, PortfolioForm
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
    paginate_by = 6
    extra_context = {
        'title': 'Все категории услуг',
        'description': 'Все доступные категории услуг'
    }

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role in ['admin', 'moderator']:
            return Category.objects.all()
        return Category.objects.filter(is_active=True, is_moderated=True)


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

        context['categories'] = Category.objects.filter(is_active=True, is_moderated=True)

        services = Service.objects.filter(category=category, is_active=True)

        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        location = self.request.GET.get('location')

        if price_min:
            services = services.filter(price__gte=price_min)
        if price_max:
            services = services.filter(price__lte=price_max)
        if location:
            services = services.filter(location__icontains=location)

        paginator = Paginator(services.order_by('-created_at'), 10)
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
    model = Category
    template_name = 'services/all_search_results.html'
    extra_context = {'title': 'Результат поискового запроса'}

    def get_queryset(self):
        query = self.request.GET.get('q')
        service_list = Service.objects.filter(Q(title__icontains=query))
        category_list = Category.objects.filter(Q(name__icontains=query))
        return list(service_list) + list(category_list)


class ServiceListView(ListView):
    model = Service
    extra_context = {
        'title': 'Все наши услуги',
        'description': 'Каждый мастер в нашем сервисе ждет своего клиента.'
    }
    template_name = 'services/services.html'
    paginate_by = 3

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


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