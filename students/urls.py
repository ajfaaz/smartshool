from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.add_student, name='add_student'),
    path('reset-password/<int:id>/', views.reset_student_password, name='reset_student_password'),

    path('edit/<int:id>/', views.edit_student, name='edit_student'),
    path('delete/<int:id>/', views.delete_student, name='delete_student'),
    path('id-card/<int:student_id>/', views.student_id_card, name='student_id_card'),
    path('parents/', views.parent_list, name='parent_list'),
    path('parents/add/', views.add_parent, name='add_parent'),
    path('parents/reset-password/<int:id>/', views.reset_parent_password, name='reset_parent_password'),
    path('parents/edit/<int:id>/', views.edit_parent, name='edit_parent'),
    path('parents/delete/<int:id>/', views.delete_parent, name='delete_parent'),
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('parent/login/', views.parent_login, name='parent_login'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),


]
