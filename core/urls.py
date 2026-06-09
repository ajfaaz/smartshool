from django.urls import path
from . import views

urlpatterns = [

path('portals/', views.portals, name='portals'),
path('dashboard/', views.dashboard, name='dashboard'),
path('settings/', views.school_settings, name='school_settings'),
path('account/settings/', views.account_settings, name='account_settings'),
path('account/password/', views.change_password, name='change_password'),
path('account/forgot-password/', views.forgot_password, name='forgot_password'),
path('account/reset/<str:role>/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
path('settings/profile/', views.update_school_profile, name='update_school_profile'),
path('settings/sessions/create/', views.create_session, name='create_session'),
path('settings/sessions/delete/<int:id>/', views.delete_session, name='delete_session'),
path('settings/terms/create/', views.create_term, name='create_term'),
path('settings/terms/delete/<int:id>/', views.delete_term, name='delete_term'),
path('settings/fees/create/', views.create_fee_structure, name='create_fee_structure'),
path('settings/fees/delete/<int:id>/', views.delete_fee_structure, name='delete_fee_structure'),
path('platform/', views.platform_dashboard, name='platform_dashboard'),
path('logout/', views.logout_view, name='logout'),
path('platform/login/', views.platform_login, name='platform_login'),
path('school-admin/login/', views.school_admin_login, name='school_admin_login'),
path('principal/login/', views.principal_login, name='principal_login'),
path('exam-officer/login/', views.exam_officer_login, name='exam_officer_login'),
path('principal/dashboard/', views.principal_dashboard, name='principal_dashboard'),
path('exam-officer/dashboard/', views.exam_officer_dashboard, name='exam_officer_dashboard'),
path('platform/schools/create/', views.create_school, name='create_school'),
path('platform/school-admins/create/', views.create_school_admin, name='create_school_admin'),
path('platform/subscriptions/create/', views.create_subscription, name='create_subscription'),
path('settings/principals/create/', views.create_principal, name='create_principal'),
path('settings/exam-officers/create/', views.create_exam_officer, name='create_exam_officer'),
path('schools/switch/', views.switch_school, name='switch_school'),

]
