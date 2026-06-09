from django.urls import path
from . import views

urlpatterns = [

    path('', views.teacher_list, name='teacher_list'),
    path('login/', views.teacher_login, name='teacher_login'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    path('add/', views.add_teacher, name='add_teacher'),
    path('edit/<int:id>/', views.edit_teacher, name='edit_teacher'),
    path('reset-password/<int:id>/', views.reset_teacher_password, name='reset_teacher_password'),

    path('delete/<int:id>/', views.delete_teacher, name='delete_teacher'),

]
