from django.contrib import admin
from .models import (
    Student, Subject, ClassSchedule, Attendance, Exam, ExamSchedule,
    ExamResult, Homework, HomeworkSubmission, FeeType, FeeAssignment,
    FeePayment, Notice, Event, Teacher,TeacherAttendance,ClassTeacher,TeacherSchedule
)

admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(ClassSchedule)
admin.site.register(Attendance)
admin.site.register(Exam)
admin.site.register(ExamSchedule)
admin.site.register(ExamResult)
admin.site.register(Homework)
admin.site.register(HomeworkSubmission)
admin.site.register(FeeType)
admin.site.register(FeeAssignment)
admin.site.register(FeePayment)

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'target', 'target_class', 'published_date', 'expiry_date', 'is_active']
    list_filter = ['priority', 'target', 'is_active']
    search_fields = ['title', 'content']
    list_editable = ['is_active']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ['title', 'category', 'event_date', 'end_date', 'target', 'target_class', 'venue', 'is_active']
    list_filter   = ['category', 'target', 'is_active']
    search_fields = ['title', 'description', 'venue']
    list_editable = ['is_active']
    ordering      = ['event_date']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'subject', 'phone']
    search_fields = ['name', 'employee_id']

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display  = ['teacher', 'date', 'status', 'remarks']
    list_filter   = ['status', 'date', 'teacher']
    search_fields = ['teacher__name']
    list_editable = ['status']
    ordering      = ['-date']
    date_hierarchy = 'date'

@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display  = ['teacher', 'class_name', 'assigned_by', 'assigned_at']
    search_fields = ['teacher__name', 'class_name']

admin.site.register(TeacherSchedule)
