from django.urls import path
from services.views import (
    index, CategoryListView, ServicesByCategoryListView, ServiceListView,
    ServiceCreateView, ServiceDetailView, ServiceUpdateView, ServiceDeleteView,
    service_toggle_activity, ServiceDeactivatedListView, ServiceSearchListView,
    CategorySearchListView, AllSearchView,
    CategoryCreateView, CategoryUpdateView, CategoryDeleteView, CategorySuggestView, CategoryModerateView, ServiceByMasterListView, PortfolioCreateView
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
    path('categories/<int:pk>/services/', cache_page(60)(ServicesByCategoryListView.as_view()), name='category_services'),
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

    path('master/<int:pk>/services/', ServiceByMasterListView.as_view(), name='master_services'),

    path('portfolio/create/', PortfolioCreateView.as_view(), name='portfolio_create'),
]
