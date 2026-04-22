from django.urls import path
from services.views import (
    index, CategoryListView, ServicesByCategoryListView, ServiceListView,
    ServiceCreateView, ServiceDetailView, ServiceUpdateView, ServiceDeleteView,
    service_toggle_activity, ServiceDeactivatedListView, ServiceSearchListView,
    CategorySearchListView, AllSearchView
)
from services.apps import ServicesConfig
from django.views.decorators.cache import cache_page, never_cache

app_name = ServicesConfig.name

urlpatterns = [
    path('', cache_page(60)(index), name='index'),

    path('categories/', cache_page(60)(CategoryListView.as_view()), name='categories'),
    path('categories/<int:pk>/services/', cache_page(60)(ServicesByCategoryListView.as_view()), name='category_services'),
    path('categories/search/', CategorySearchListView.as_view(), name='categories_search'),
    path('all_search/', AllSearchView.as_view(), name='all_search'),

    path('services/', ServiceListView.as_view(), name='services_list'),
    path('services/deactivate/', ServiceDeactivatedListView.as_view(), name='services_list_deactivated'),
    path('services/search/', ServiceSearchListView.as_view(), name='services_search'),
    path('services/create/', never_cache(ServiceCreateView.as_view()), name='service_create'),
    path('services/detail/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('services/update/<int:pk>/', never_cache(ServiceUpdateView.as_view()), name='service_update'),
    path('services/toggle/<int:pk>/', service_toggle_activity, name='service_toggle_activity'),
    path('services/delete/<int:pk>/', ServiceDeleteView.as_view(), name='service_delete'),
]
