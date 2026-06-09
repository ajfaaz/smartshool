from django.urls import path
from . import views

urlpatterns = [
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('history/', views.view_attendance_history, name='view_attendance_history'),
]