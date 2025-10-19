from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/stats/', views.get_dashboard_stats, name='dashboard_stats'),
    
    # Ijaralar
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/create/', views.create_rental, name='create_rental'),
    path('rentals/<int:rental_id>/', views.rental_detail, name='rental_detail'),
    path('rentals/<int:rental_id>/items/', views.add_rental_items, name='add_rental_items'),
    path('rentals/<int:rental_id>/complete/', views.complete_rental, name='complete_rental'),
    
    # Asboblar
    path('tools/', views.tool_list, name='tool_list'),
    path('tools/create/', views.create_tool, name='create_tool'),
    
    # Mijozlar
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),
     path('tools/<int:tool_id>/edit/', views.edit_tool, name='edit_tool'),
    path('tools/<int:tool_id>/delete/', views.delete_tool, name='delete_tool'),
    
    # Mijozlar
    path('customers/<int:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    path('customers/<int:customer_id>/delete/', views.delete_customer, name='delete_customer'),
    
    # Ijaralar
    path('rentals/<int:rental_id>/edit/', views.edit_rental, name='edit_rental'),
    path('rentals/<int:rental_id>/delete/', views.delete_rental, name='delete_rental'),
]