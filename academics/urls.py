from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/delete/<int:id>/', views.delete_class, name='delete_class'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/delete/<int:id>/', views.delete_subject, name='delete_subject'),
    path('assignments/', views.teacher_subject_list, name='teacher_subject_list'),
    path('assign-teacher/', views.assign_teacher, name='assign_teacher'),
    path('results/', views.result_list, name='result_list'),
    path('results/<int:result_id>/principal-comment/', views.update_principal_comment, name='update_principal_comment'),
    path('results/add/', views.add_result, name='add_result'),
    path('enter-results/', views.enter_results, name='enter_results'),
    path('positions/', views.class_positions, name='positions'),
    path('report/<int:student_id>/pdf/', views.generate_report_pdf, name='academics_report_pdf'),
    path("bulk-results/", views.bulk_result_entry, name="bulk_result_entry"),
    path('promote/', views.promote_students, name='promote_students'),
    path('assignments/list/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),


]
