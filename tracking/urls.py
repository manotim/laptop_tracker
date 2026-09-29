from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/<int:laptop_id>/', views.checkout_laptop, name='checkout'),
    path('return/<int:checkout_id>/', views.return_laptop, name='return_laptop'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
]