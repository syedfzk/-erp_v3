"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/',             views.login_view,        name='login_view'),
    path('logout/',            views.logout_view,        name='student_logout'),
    path('student/dashboard/', views.student_dashboard,  name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/timetable/', views.student_timetable, name='student_timetable'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/homework/', views.student_homework, name='student_homework'),
    path('student/homework/submit/<int:homework_id>/', views.submit_homework, name='submit_homework'),
    path('student/fees/', views.student_fees, name='student_fees'),
    path('student/notices/', views.student_notices, name='student_notices'),
    path('student/events/', views.student_events, name='student_events'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/timetable/', views.teacher_timetable, name='teacher_timetable'),
    path('teacher/attendance/mark/',    views.teacher_mark_attendance,     name='teacher_mark_attendance'),
    path('teacher/attendance/mine/',    views.teacher_my_attendance,       name='teacher_my_attendance'),
    path('teacher/myclass/', views.teacher_my_class, name='teacher_my_class'),
    path('teacher/myclass/', views.teacher_my_class, name='teacher_my_class'),
    path('teacher/myclass/results/pdf/', views.class_results_pdf, name='class_results_pdf'),
    path('teacher/student/<int:student_id>/result/pdf/', views.student_result_pdf, name='student_result_pdf'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)