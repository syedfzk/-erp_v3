from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection
from datetime import datetime, date, timedelta
from .models import Student
from django.contrib.auth import authenticate, login, logout
 



def home(request):
    return render(request, 'index.html')

@login_required
def student_dashboard(request):
    student = Student.objects.get(user=request.user) 

    # Today's classes
    today_name = datetime.now().strftime('%A')
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetTodayClasses @class_name = %s, @day_of_week = %s",
            [student.class_name, today_name]
        )
        rows = cursor.fetchall()
        classes = [
            {
                'id':         r[0],
                'subject':    r[1],
                'teacher':    r[2],
                'start_time': r[3],
                'end_time':   r[4],
                'status':     r[5],
            }
            for r in rows
        ]

    # Attendance
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentAttendance @student_id = %s",
            [student.id]
        )
        row = cursor.fetchone()
        total    = row[0] if row else 0
        present  = row[1] if row else 0
        absent   = row[2] if row else 0
        half_day = row[3] if row else 0

        cursor.nextset()
        day_rows = cursor.fetchall()

    day_labels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    last_7_days = []
    for r in day_rows:
        date_obj = r[0]
        status   = r[1]
        label    = day_labels[date_obj.weekday()]
        if status == 'Present':
            badge = 'bg-success'
        elif status == 'Absent':
            badge = 'bg-danger'
        elif status == 'Half-Day':
            badge = 'bg-warning'
        else:
            badge = 'bg-white border text-default'
        last_7_days.append({'label': label, 'badge_class': badge})

    today_date = date.today()
    week_start = today_date - timedelta(days=6)
    week_range = f"{week_start.strftime('%d %b %Y')} - {today_date.strftime('%d %b %Y')}"

    attendance = {
        'total':       total,
        'present':     present,
        'absent':      absent,
        'half_day':    half_day,
        'last_7_days': last_7_days,
        'week_range':  week_range,
    }

    # Exam schedule
    exams = []
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentExamSchedule @class_name = %s",
            [student.class_name]
        )
        rows = cursor.fetchall()
        for r in rows:
            print("CLASS ROW:", r)
            exams.append({
                'exam_name':     r[0],
                'subject_name':  r[1],
                'exam_date':     r[2],
                'start_time':    r[3],
                'end_time':      r[4],
                'room_number':   r[5],
                'days_remaining': r[6],
            })

    # ONE return at the end
    return render(request, 'student-dashboard.html', {
        'student':    student,
        'classes':    classes,
        'attendance': attendance,
        'exams':      exams,
    })

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('student_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

def student_logout(request):
    logout(request)
    return redirect('student_login')