"""
URL configuration for school_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from academics import views as academic_views
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return render(request, "home.html")

urlpatterns = [

path('admin/', admin.site.urls),

path('', home, name='home'),

path('', include('core.urls')),

path('students/', include('students.urls')),

path('academics/', include('academics.urls')),

path('teachers/', include('teachers.urls')),

path('report/<int:student_id>/pdf', academic_views.generate_report_pdf, name='report_pdf'),
path("finance/", include("finance.urls")),

path('attendance/', include('attendance.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
