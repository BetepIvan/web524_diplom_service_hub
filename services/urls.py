from django.urls import path
from services.views import (
    index, CategoryListView, ServicesByCategoryListView, ServiceListView,
    ServiceCreateView, ServiceDetailView, ServiceUpdateView, ServiceDeleteView,
    service_toggle_activity, ServiceDeactivatedListView, ServiceSearchListView,
    CategorySearchListView, AllSearchView,
    CategoryCreateView, CategoryUpdateView, CategoryDeleteView, CategorySuggestView, CategoryModerateView,
    PortfolioCreateView, ServiceLibraryListView, MasterServiceCreateView, MyServicesListView,
    MasterServiceDeleteView, MasterServiceToggleView, MasterServicesListView, ServiceTemplateCreateView
)
from services.apps import ServicesConfig
from django.views.decorators.cache import cache_page, never_cache

app_name = ServicesConfig.name

urlpatterns = [
    path('', cache_page(60)(index), name='index'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='categories_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/suggest/', CategorySuggestView.as_view(), name='category_suggest'),
    path('categories/<int:pk>/services/', cache_page(60)(ServicesByCategoryListView.as_view()),
         name='category_services'),
    path('categories/search/', CategorySearchListView.as_view(), name='categories_search'),
    path('categories/<int:pk>/moderate/', CategoryModerateView.as_view(), name='category_moderate'),

    path('all_search/', AllSearchView.as_view(), name='all_search'),

    # Services
    path('services/', ServiceListView.as_view(), name='services_list'),
    path('services/deactivate/', ServiceDeactivatedListView.as_view(), name='services_list_deactivated'),
    path('services/search/', ServiceSearchListView.as_view(), name='services_search'),
    path('services/create/', never_cache(ServiceCreateView.as_view()), name='service_create'),
    path('services/detail/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('services/update/<int:pk>/', never_cache(ServiceUpdateView.as_view()), name='service_update'),
    path('services/toggle/<int:pk>/', service_toggle_activity, name='service_toggle_activity'),
    path('services/delete/<int:pk>/', ServiceDeleteView.as_view(), name='service_delete'),

    # Service Library
    path('services/library/', ServiceLibraryListView.as_view(), name='service_library'),
    path('services/library/add/<int:pk>/', MasterServiceCreateView.as_view(), name='master_service_add'),
    path('services/template/create/', ServiceTemplateCreateView.as_view(), name='service_template_create'),

    # Master Services
    path('master/<int:pk>/services/', MasterServicesListView.as_view(), name='master_services'),

    # My Services
    path('my-services/', MyServicesListView.as_view(), name='my_services'),
    path('my-services/delete/<int:pk>/', MasterServiceDeleteView.as_view(), name='master_service_delete'),
    path('my-services/toggle/<int:pk>/', MasterServiceToggleView.as_view(), name='master_service_toggle'),

    # Portfolio
    path('portfolio/create/', PortfolioCreateView.as_view(), name='portfolio_create'),
]
