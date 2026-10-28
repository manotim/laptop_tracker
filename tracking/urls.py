from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/<int:laptop_id>/', views.checkout_laptop, name='checkout'),
    path('return/<int:checkout_id>/', views.return_laptop, name='return_laptop'),

    # staff
    path('staff/', views.staff_dashboard, name='staff_dashboard'),

    path('staff/laptops/', views.staff_laptops_list, name='staff_laptops'),
    path('staff/laptops/add/', views.staff_laptop_form, name='staff_laptop_add'),
    path('staff/laptops/<int:laptop_id>/', views.staff_laptop_detail, name='staff_laptop_detail'),
    path('staff/laptops/<int:laptop_id>/edit/', views.staff_laptop_form, name='staff_laptop_edit'),
    path('staff/laptops/<int:laptop_id>/checkout/', views.staff_laptop_checkout, name='staff_laptop_checkout'),
    path('staff/laptops/<int:laptop_id>/return/', views.staff_laptop_return, name='staff_laptop_return'),

    path('staff/students/', views.staff_students_list, name='staff_students'),
    path('staff/students/add/', views.staff_student_form, name='staff_student_add'),
    path('staff/students/<int:student_id>/edit/', views.staff_student_form, name='staff_student_edit'),

    path('staff/laptops/<int:laptop_id>/delete/', views.staff_laptop_delete, name='staff_laptop_delete'),
    path('staff/students/<int:student_id>/delete/', views.staff_student_delete, name='staff_student_delete'),
]