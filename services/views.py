from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import inlineformset_factory
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from services.models import Category, Service, ServiceImage
from services.forms import ServiceForm, ServiceCreateForm, ServiceAdminForm, ServiceImageForm
from services.services import send_views_mail
from users.services import send_service_creation  # нужно будет переименовать в users/services.py
from users.models import UserRoles


def index(request):
    context = {
        'object_list': Category.objects.all()[:3],
        'title': 'Услуги мастеров - Главная',
        'description': 'Добро пожаловать на платформу услуг мастеров! Здесь вы найдете лучших специалистов в своем деле, информацию о каждой услуге, а также сможете выбрать себе профессионала.'
    }
    return render(request, 'services/index.html', context)


class CategoryListView(ListView):
    model = Category
    extra_context = {
        'title': 'Все категории услуг',
        'description': 'Сантехника, электрика, ремонт, клининг и многое другое — все в одном месте. Изучайте категории, знакомьтесь с мастерами и выбирайте того, кто вам подходит.'
    }
    template_name = 'services/categories.html'
    paginate_by = 3


class ServicesByCategoryListView(ListView):
    model = Service
    template_name = 'services/services.html'
    extra_context = {
        'title': 'Услуги выбранной категории'
    }
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset().filter(category_id=self.kwargs.get('pk'))
        queryset = queryset.filter(is_active=True)
        return queryset


class CategorySearchListView(ListView):
    model = Category
    template_name = 'services/categories.html'
    extra_context = {
        'title': 'Результаты поиска категорий'
    }

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = Category.objects.filter(
            Q(name__icontains=query)
        )
        return object_list


class AllSearchView(ListView):
    model = Category
    template_name = 'services/all_search_results.html'

    extra_context = {
        'title': 'Результат поискового запроса'
    }

    def get_queryset(self):
        query = self.request.GET.get('q')
        service_object_list = Service.objects.filter(
            Q(title__icontains=query)
        )
        category_object_list = Category.objects.filter(
            Q(name__icontains=query)
        )
        object_list = list(service_object_list) + list(category_object_list)
        return object_list


class ServiceListView(ListView):
    model = Service
    extra_context = {
        'title': 'Все наши услуги',
        'description': 'Каждый мастер в нашем сервисе ждет своего клиента. Профессионалы своего дела — мы расскажем о каждой услуге, чтобы вы нашли идеального специалиста.'
    }
    template_name = 'services/services.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


class ServiceDeactivatedListView(LoginRequiredMixin, ListView):
    model = Service
    extra_context = {
        'title': 'Неактивные услуги'
    }
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
    extra_context = {
        'title': 'Результаты поиска услуг'
    }

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = Service.objects.filter(
            Q(title__icontains=query), is_active=True,
        )
        return object_list


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceCreateForm
    template_name = 'services/create_update.html'
    extra_context = {
        'title': 'Добавить услугу'
    }
    success_url = reverse_lazy('services:services_list')

    def form_valid(self, form):
        if self.request.user.role != UserRoles.USER:
            raise PermissionDenied()
        service_object = form.save()
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
        user_role = self.request.user.role
        service_forms_class = service_forms[user_role]
        return service_forms_class

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        ServiceImageFormset = inlineformset_factory(Service, ServiceImage, form=ServiceImageForm, extra=1)
        if self.request.method == 'POST':
            formset = ServiceImageFormset(self.request.POST, self.request.FILES, instance=self.object)
        else:
            formset = ServiceImageFormset(instance=self.object)
        get_object = self.get_object()
        context_data['formset'] = formset
        context_data['title'] = f'Изменить\n{get_object}'
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
        # Может редактировать только владелец
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
        service_object = self.get_object()
        context_data['title'] = f'Удалить\n{service_object}'
        return context_data


def service_toggle_activity(request, pk):
    service_object = get_object_or_404(Service, pk=pk)
    if service_object.is_active:
        service_object.is_active = False
    else:
        service_object.is_active = True
    service_object.save()
    return redirect(reverse('services:services_list'))