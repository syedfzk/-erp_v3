from django.contrib import admin
from .models import Student, Subject, ClassSchedule,Attendance,Exam, ExamSchedule

admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(ClassSchedule)
admin.site.register(Attendance)
admin.site.register(Exam)
admin.site.register(ExamSchedule)