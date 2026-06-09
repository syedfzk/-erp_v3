from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import connection
from datetime import datetime, date, timedelta
from .models import Student,HomeworkSubmission,FeeAssignment,FeePayment,FeeType,Exam, ExamSchedule, ExamResult,Teacher,Subject,Attendance,ClassTeacher,Homework,Notice,Event,HomeworkSubmission
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, date, timedelta
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm





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
    
        # Homework
        homework = []
        with connection.cursor() as cursor:
              cursor.execute(
                  "EXEC sp_GetStudentHomework @class_name = %s, @student_id = %s",
                 [student.class_name, student.id]
             )
              rows = cursor.fetchall()
              for r in rows:
                homework.append({
                   'id':                r[0],
                   'subject':           r[1],
                   'title':             r[2],
                   'description':       r[3],
                   'due_date':          r[4],
                   'attachment':        r[5],
                   'priority':          r[6],
                   'created_at':        r[7],
                   'submission_status': r[8],
                   'due_status':        r[9],
        })
        
        # Notice Board
        notices = []
        with connection.cursor() as cursor:
              cursor.execute(
                  "EXEC sp_GetStudentNotices @class_name = %s, @page = 1, @page_size = 5",
                 [student.class_name]
             )
              rows = cursor.fetchall()
              for r in rows:
               notices.append({
                'id':             r[0],
                'title':          r[1],
                'content':        r[2],
                'priority':       r[3],
                'published_date': r[6],
                'days_ago':       r[10],
                'is_new':         r[11],
                'expiring_soon':  r[12],
        })
        
        # Exam Results
        exam_results = []
        with connection.cursor() as cursor:
              cursor.execute(
                  "EXEC sp_GetStudentExamResults @student_id = %s",
                [student.id]
             )
              rows = cursor.fetchall()
              for r in rows:
               exam_results.append({
            'exam_name':      r[0],
            'subject_name':   r[1],
            'max_marks':      r[2],
            'obtained_marks': r[3],
            'grade':          r[4],
            'result':         r[5],
            'percentage':     r[6],
        })

    # ONE return at the end
    return render(request, 'student-dashboard.html', {
        'student':    student,
        'classes':    classes,
        'attendance': attendance,
        'exams':      exams,
        'homework':   homework,
        'notices':    notices,
        'exam_results': exam_results,
    })


def login_view(request):
    if request.user.is_authenticated:
        try:
            Student.objects.get(user=request.user)
            return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass
        try:
            Teacher.objects.get(user=request.user)
            return redirect('teacher_dashboard')
        except Teacher.DoesNotExist:
            pass

    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')

        try:
            from django.contrib.auth.models import User
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            try:
                Student.objects.get(user=user)
                return redirect('student_dashboard')
            except Student.DoesNotExist:
                pass
            try:
                Teacher.objects.get(user=user)
                return redirect('teacher_dashboard')
            except Teacher.DoesNotExist:
                pass
            logout(request)
            return render(request, 'login.html', {
                'error': 'No role assigned. Contact admin.'
            })
        else:
            return render(request, 'login.html', {
                'error': 'Invalid email or password.'
            })

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login_view')

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

@login_required
def student_profile(request):
    student = Student.objects.get(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Update personal info (email + phone)
        if action == 'update_info':
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            # Update email in User model
            request.user.email = email
            request.user.save()

            # Update phone in Student model
            student.phone = phone
            student.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')

        # Update profile photo
        elif action == 'update_photo':
            if 'profile_image' in request.FILES:
                student.profile_image = request.FILES['profile_image']
                student.save()
                messages.success(request, 'Profile photo updated!')
                return redirect('student_profile')

        # Change password
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password     = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # keeps user logged in
                messages.success(request, 'Password changed successfully!')
            return redirect('student_profile')

    return render(request, 'profile.html', {
        'student': student,
    })

from calendar import monthrange
import calendar

@login_required
def student_attendance(request):
    student = Student.objects.get(user=request.user)

    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentAttendanceMonthly @student_id=%s, @month=%s, @year=%s",
            [student.id, month, year]
        )
        # Result Set 1 — summary
        row = cursor.fetchone()
        summary = {
            'total':      row[0] if row else 0,
            'present':    row[1] if row else 0,
            'absent':     row[2] if row else 0,
            'half_day':   row[3] if row else 0,
            'percentage': round((row[1] / row[0] * 100), 1) if row and row[0] > 0 else 0,
        }

        # Result Set 2 — daily detail
        cursor.nextset()
        day_rows = cursor.fetchall()

    # Build dict {day_number: status}
    attendance_map = {}
    for r in day_rows:
        attendance_map[r[0]] = r[1]

    # Build full month days list
    _, days_in_month = monthrange(year, month)
    month_days = []
    for d in range(1, days_in_month + 1):
        status = attendance_map.get(d, None)
        if status == 'Present':
            css = 'bg-success'
        elif status == 'Absent':
            css = 'bg-danger'
        elif status == 'Half-Day':
            css = 'bg-dark'
        else:
            css = 'bg-light border'
        day_obj = date(year, month, d)
        month_days.append({
            'day':    d,
            'label':  day_obj.strftime('%a')[0],
            'css':    css,
            'status': status,
        })

    # Previous and next month navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    month_name = calendar.month_name[month]

    return render(request, 'students-sidebar-attendance.html', {
        'student':    student,
        'summary':    summary,
        'month_days': month_days,
        'month':      month,
        'year':       year,
        'month_name': month_name,
        'prev_month': prev_month,
        'prev_year':  prev_year,
        'next_month': next_month,
        'next_year':  next_year,
    })

@login_required
def student_timetable(request):
    student = Student.objects.get(user=request.user)

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentTimetable @class_name = %s",
            [student.class_name]
        )
        rows = cursor.fetchall()

    # Group by day
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable = {day: [] for day in days_order}

    # Cycle through colors for cards
    colors = [
        'bg-transparent-danger',
        'bg-transparent-primary',
        'bg-transparent-success',
        'bg-transparent-pending',
        'bg-transparent-info',
        'bg-transparent-light',
        'bg-transparent-warning',
    ]

    color_index = {}  # track color per day

    for r in rows:
        day        = r[0]
        subject    = r[1]
        teacher    = r[2]
        start_time = r[3]
        end_time   = r[4]
        status     = r[5]

        if day not in timetable:
            continue

        # Assign color cycling per day
        if day not in color_index:
            color_index[day] = 0
        color = colors[color_index[day] % len(colors)]
        color_index[day] += 1

        timetable[day].append({
            'subject':    subject,
            'teacher':    teacher,
            'start_time': start_time,
            'end_time':   end_time,
            'status':     status,
            'color':      color,
        })

    # Only include days that have classes
    timetable_filtered = {day: classes for day, classes in timetable.items() if classes}

    return render(request, 'class-time-table.html', {
        'student':   student,
        'timetable': timetable_filtered,
    })

@login_required
def student_results(request):
    student = Student.objects.get(user=request.user)
    
    results = []
    exams = {}
    
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentExamResults @student_id = %s",
            [student.id]
        )
        rows = cursor.fetchall()
        for r in rows:
            exam_name = r[0]
            if exam_name not in exams:
                exams[exam_name] = []
            exams[exam_name].append({
                'subject_name':    r[1],
                'max_marks':       r[2],
                'obtained_marks':  r[3],
                'grade':           r[4],
                'result':          r[5],
                'percentage':      r[6],
            })

    return render(request, 'student-results.html', {
        'student': student,
        'exams':   exams,
    })


@login_required
def student_homework(request):
    student = Student.objects.get(user=request.user)

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentHomework @class_name = %s, @student_id = %s",
            [student.class_name, student.id]
        )
        rows = cursor.fetchall()

    homework_list = []
    for r in rows:
        homework_list.append({
            'id':                r[0],
            'subject_name':      r[1],
            'title':             r[2],
            'description':       r[3],
            'due_date':          r[4],
            'attachment':        r[5],
            'priority':          r[6],
            'created_at':        r[7],
            'submission_status': r[8],
            'due_status':        r[9],
        })

    # Split into pending and submitted
    pending   = [h for h in homework_list if h['submission_status'] == 'Pending']
    submitted = [h for h in homework_list if h['submission_status'] != 'Pending']

    return render(request, 'student-homework.html', {
        'student':   student,
        'pending':   pending,
        'submitted': submitted,
        'total':     len(pending) + len(submitted),
    })


@login_required
@require_POST
def submit_homework(request, homework_id):
    student = Student.objects.get(user=request.user)
    comments = request.POST.get('comments', '')
    submission_file = request.FILES.get('submission_file')

    # Save file if uploaded
    submission = None
    if HomeworkSubmission.objects.filter(
        homework_id=homework_id, student=student
    ).exists():
        submission = HomeworkSubmission.objects.get(
            homework_id=homework_id, student=student
        )
        submission.comments = comments
        submission.status = 'Submitted'
        if submission_file:
            submission.submission_file = submission_file
        submission.save()
    else:
        submission = HomeworkSubmission.objects.create(
            homework_id=homework_id,
            student=student,
            comments=comments,
            submission_file=submission_file,
            status='Submitted'
        )

    return redirect('student_homework')

@login_required
def student_fees(request):
    student = Student.objects.get(user=request.user)

    available_years = list(
        FeeAssignment.objects
        .filter(student=student)
        .values_list('academic_year', flat=True)
        .distinct()
        .order_by('-academic_year')
    )

    default_year = available_years[0] if available_years else None
    academic_year = request.GET.get('year', default_year)

    if not academic_year:
        return render(request, 'student-fees.html', {
            'student': student,
            'summary': None,
            'fee_rows': [],
            'payments': [],
            'academic_year': None,
            'available_years': [],
        })

    summary = {}
    fee_rows = []
    payments = []

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentFees @student_id = %s, @academic_year = %s",
            [student.id, academic_year]
        )

        raw = cursor.cursor

        while True:
            if raw.description:
                cols = [col[0] for col in raw.description]
                rows = raw.fetchall()

                if 'total_fees' in cols:
                    if rows:
                        summary = dict(zip(cols, rows[0]))

                elif 'assignment_id' in cols:
                    fee_rows = [dict(zip(cols, row)) for row in rows]

                elif 'receipt_number' in cols:
                    payments = [dict(zip(cols, row)) for row in rows]

            if not raw.nextset():
                break

    return render(request, 'student-fees.html', {
        'student': student,
        'summary': summary,
        'fee_rows': fee_rows,
        'payments': payments,
        'academic_year': academic_year,
        'available_years': available_years,
    })

@login_required
def student_notices(request):
    student = get_object_or_404(Student, user=request.user)
    
    page = int(request.GET.get('page', 1))
    priority_filter = request.GET.get('priority', '')  # optional filter
    page_size = 8

    notices = []
    total_count = 0
    priority_counts = {'urgent': 0, 'high': 0, 'normal': 0, 'low': 0}

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_GetStudentNotices @class_name = %s, @page = %s, @page_size = %s",
                [student.class_name, page, page_size]
            )
            raw = cursor.cursor  # raw pyodbc cursor

            while True:
                if raw.description:
                    cols = [col[0] for col in raw.description]
                    rows = raw.fetchall()

                    if 'title' in cols and 'priority' in cols:
                        # Result set 1: notices list
                        all_notices = [dict(zip(cols, r)) for r in rows]
                        # Apply priority filter client-side if needed
                        if priority_filter:
                            notices = [n for n in all_notices if n['priority'] == priority_filter]
                        else:
                            notices = all_notices

                    elif 'total_count' in cols:
                        # Result set 2: pagination total
                        total_count = rows[0][0] if rows else 0

                    elif 'cnt' in cols:
                        # Result set 3: priority breakdown
                        for row in rows:
                            d = dict(zip(cols, row))
                            priority_counts[d['priority']] = d['cnt']

                if not raw.nextset():
                    break

    except Exception as e:
        messages.error(request, f"Error loading notices: {str(e)}")

    total_pages = (total_count + page_size - 1) // page_size

    context = {
        'student': student,
        'notices': notices,
        'total_count': total_count,
        'priority_counts': priority_counts,
        'current_page': page,
        'total_pages': total_pages,
        'priority_filter': priority_filter,
        'page_range': range(1, total_pages + 1),
    }
    return render(request, 'student-notices.html', context)

@login_required
def student_events(request):
    student = get_object_or_404(Student, user=request.user)

    category_filter = request.GET.get('category', '')
    show_past       = request.GET.get('past', '0') == '1'

    upcoming_events = []
    past_events     = []
    category_counts = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_GetStudentEvents @class_name = %s",
                [student.class_name]
            )
            raw = cursor.cursor

            while True:
                if raw.description:
                    cols = [col[0] for col in raw.description]
                    rows = raw.fetchall()

                    if 'days_until' in cols:
                        # Result set 1: upcoming
                        all_upcoming = [dict(zip(cols, r)) for r in rows]
                        if category_filter:
                            upcoming_events = [e for e in all_upcoming if e['category'] == category_filter]
                        else:
                            upcoming_events = all_upcoming

                    elif 'days_ago' in cols:
                        # Result set 2: past
                        past_events = [dict(zip(cols, r)) for r in rows]

                    elif 'cnt' in cols:
                        # Result set 3: category counts
                        for row in rows:
                            d = dict(zip(cols, row))
                            category_counts[d['category']] = d['cnt']

                if not raw.nextset():
                    break

    except Exception as e:
        messages.error(request, f"Error loading events: {str(e)}")

    # Pull out today/tomorrow for highlight strip
    today_events    = [e for e in upcoming_events if e['when_label'] == 'today']
    tomorrow_events = [e for e in upcoming_events if e['when_label'] == 'tomorrow']
    this_week       = [e for e in upcoming_events if e['when_label'] == 'this_week']
    later_events    = [e for e in upcoming_events if e['when_label'] == 'upcoming']

    context = {
        'student':          student,
        'today_events':     today_events,
        'tomorrow_events':  tomorrow_events,
        'this_week':        this_week,
        'later_events':     later_events,
        'past_events':      past_events,
        'category_counts':  category_counts,
        'category_filter':  category_filter,
        'show_past':        show_past,
        'total_upcoming':   len(upcoming_events),
        'CATEGORY_ICONS': {
            'academic':  'mdi-book-open-variant',
            'sports':    'mdi-trophy',
            'cultural':  'mdi-palette',
            'holiday':   'mdi-beach',
            'exam':      'mdi-pencil-box',
            'other':     'mdi-calendar-star',
        },
        'CATEGORY_COLORS': {
            'academic':  'primary',
            'sports':    'success',
            'cultural':  'warning',
            'holiday':   'info',
            'exam':      'danger',
            'other':     'secondary',
        },
    }
    return render(request, 'student-events.html', context)

from .models import Student, Teacher

# ============================================================
#  REPLACE your teacher_dashboard view in core/views.py
# ============================================================

@login_required
def teacher_dashboard(request):
    teacher = Teacher.objects.get(user=request.user)

    today_name = datetime.now().strftime('%A')
    hour = datetime.now().hour
    if hour < 12:
        greeting = 'Morning'
    elif hour < 17:
        greeting = 'Afternoon'
    else:
        greeting = 'Evening'

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetTeacherTodayClasses @teacher_id = %s, @day_of_week = %s",
            [teacher.user.id, today_name]
        )
        raw = cursor.cursor
        classes = []
        if raw.description:
            cols = [col[0] for col in raw.description]
            classes = [dict(zip(cols, row)) for row in raw.fetchall()]

    return render(request, 'teacher-dashboard.html', {
        'teacher':  teacher,
        'classes':  classes,
        'today':    today_name,
        'greeting': greeting,
    })


@login_required
def teacher_timetable(request):
    teacher = Teacher.objects.get(user=request.user)
 
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetTeacherTimetable @teacher_id = %s",
            [teacher.user.id]
        )
        raw = cursor.cursor
        rows = []
        if raw.description:
            cols = [col[0] for col in raw.description]
            rows = [dict(zip(cols, row)) for row in raw.fetchall()]
 
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    today = datetime.now().strftime('%A')
 
    def fmt_time(t):
        """Format time object or timedelta to HH:MM"""
        if t is None:
            return ''
        # SQL Server returns timedelta for TIME columns via pyodbc
        if hasattr(t, 'seconds'):
            total = int(t.seconds)
            h, m = divmod(total // 60, 60)
            return f"{h:02d}:{m:02d}"
        # datetime.time object
        return t.strftime('%H:%M')
 
    # Unique time slots in order
    seen_slots = []
    for row in rows:
        slot = f"{fmt_time(row['start_time'])} - {fmt_time(row['end_time'])}"
        if slot not in seen_slots:
            seen_slots.append(slot)
 
    # Active days in correct order
    active_days = []
    for row in rows:
        if row['day_of_week'] not in active_days:
            active_days.append(row['day_of_week'])
    days = [d for d in days_order if d in active_days]
 
    # Grid entries
    grid = []
    class_list = []
    for row in rows:
        slot = f"{fmt_time(row['start_time'])} - {fmt_time(row['end_time'])}"
        grid.append({
            'slot':         slot,
            'day':          row['day_of_week'],
            'subject_name': row['subject_name'],
            'class_name':   row['class_name'],
            'status':       row['status'],
        })
        if row['class_name'] not in class_list:
            class_list.append(row['class_name'])
 
    class_list.sort()
 
    return render(request, 'teacher-timetable.html', {
        'teacher':    teacher,
        'grid':       grid,
        'time_slots': seen_slots,
        'days':       days,
        'today':      today,
        'timetable':  rows,
        'class_list': class_list,
    })
 
@login_required
def teacher_mark_attendance(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    today   = date.today()

    # Check if this teacher is a class teacher
    try:
        class_teacher = ClassTeacher.objects.get(teacher=teacher)
        assigned_class = class_teacher.class_name
    except ClassTeacher.DoesNotExist:
        # Not a class teacher — show error
        return render(request, 'teacher-mark-attendance.html', {
            'teacher':          teacher,
            'not_class_teacher': True,
            'today':            today,
        })

    students     = []
    summary      = {}
    save_success = False
    save_error   = ''

    # Handle POST
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_id')
        try:
            with connection.cursor() as cursor:
                for sid in student_ids:
                    status = request.POST.get(f'status_{sid}', 'Present')
                    cursor.execute(
                        "EXEC sp_SaveStudentAttendance @student_id=%s, @date=%s, @status=%s, @marked_by=%s",
                        [sid, str(today), status, request.user.id]
                    )
                    cursor.cursor.nextset()
            save_success = True
        except Exception as e:
            save_error = str(e)

    # Load students for assigned class
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_GetStudentsByClass @class_name=%s, @date=%s",
                [assigned_class, str(today)]
            )
            raw = cursor.cursor
            while True:
                if raw.description:
                    cols = [col[0] for col in raw.description]
                    rows = raw.fetchall()
                    if 'roll_number' in cols:
                        students = [dict(zip(cols, r)) for r in rows]
                    elif 'total_students' in cols:
                        summary = dict(zip(cols, rows[0])) if rows else {}
                if not raw.nextset():
                    break
    except Exception as e:
        save_error = str(e)

    context = {
        'teacher':        teacher,
        'assigned_class': assigned_class,
        'students':       students,
        'summary':        summary,
        'save_success':   save_success,
        'save_error':     save_error,
        'today':          today,
    }
    return render(request, 'teacher-mark-attendance.html', context)

@login_required
def teacher_my_attendance(request):
    teacher       = get_object_or_404(Teacher, user=request.user)
    month         = int(request.GET.get('month', date.today().month))
    year          = int(request.GET.get('year', date.today().year))
    selected_date = request.GET.get('date', '')
    records       = []
    summary       = {}
    error         = ''

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_GetTeacherOwnAttendance @teacher_id=%s, @month=%s, @year=%s",
                [teacher.id, month, year]
            )
            raw = cursor.cursor

            while True:
                if raw.description:
                    cols = [col[0] for col in raw.description]
                    rows = raw.fetchall()

                    if 'day_name' in cols:
                        all_records = [dict(zip(cols, r)) for r in rows]
                        # filter by date if selected
                        if selected_date:
                            try:
                                filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                                records = [
                                 r for r in all_records
                                  if r['date'] == filter_date
                             ]
                            except ValueError:
                                records = all_records
                        else:
                             records = all_records
                    elif 'total_days' in cols:
                     summary = dict(zip(cols, rows[0])) if rows else {}

                if not raw.nextset():
                    break

    except Exception as e:
        error = str(e)

    context = {
        'teacher':       teacher,
        'records':       records,
        'summary':       summary,
        'month':         month,
        'year':          year,
        'selected_date': selected_date,
        'months':        [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        'years':         range(date.today().year, date.today().year - 3, -1),
        'month_name':    datetime(year, month, 1).strftime('%B'),
        'error':         error,
    }
    return render(request, 'teacher-my-attendance.html', context)

@login_required
def teacher_my_class(request):
    teacher = Teacher.objects.get(user=request.user)

    # Class info + student list
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetMyClass @teacher_id = %s",
            [request.user.id]
        )
        # Result set 1 — class info
        row = cursor.fetchone()
        class_info = None
        if row:
            class_info = {
                'class_name':      row[0],
                'teacher_name':    row[1],
                'total_students':  row[2],
            }

        # Result set 2 — student list
        cursor.nextset()
        student_rows = cursor.fetchall()
        students = []
        for r in student_rows:
            students.append({
                'id':            r[0],
                'name':          r[1],
                'roll_number':   r[2],
                'profile_image': r[3],
                'result_status': r[4],
            })

    # Parent contacts
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetClassParents @teacher_id = %s",
            [request.user.id]
        )
        parent_rows = cursor.fetchall()
        parents = []
        for r in parent_rows:
            parents.append({
                'student_name': r[0],
                'roll_number':  r[1],
                'parent_name':  r[2],
                'relation':     r[3],
                'phone':        r[4],
                'email':        r[5],
            })

    # Attendance summary
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetClassAttendanceSummary @teacher_id = %s",
            [request.user.id]
        )
        att_rows = cursor.fetchall()
        attendance = []
        for r in att_rows:
            attendance.append({
                'id':                     r[0],
                'name':                   r[1],
                'roll_number':            r[2],
                'total_days':             r[3],
                'present':                r[4],
                'absent':                 r[5],
                'half_day':               r[6],
                'attendance_percentage':  r[7],
            })

    # Class results — grouped by student
    results_by_student = {}
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetClassResults @teacher_id = %s",
            [request.user.id]
        )
        result_rows = cursor.fetchall()
        for r in result_rows:
            student_id = r[0]
            if student_id not in results_by_student:
                results_by_student[student_id] = {
                    'id':            r[0],
                    'name':          r[1],
                    'roll_number':   r[2],
                    'result_status': r[7],
                    'subjects':      [],
                }
            if r[3]:  # if exam exists
                results_by_student[student_id]['subjects'].append({
                    'exam_name':      r[3],
                    'total_obtained': r[4],
                    'total_max':      r[5],
                    'percentage':     r[6],
                })

    print("RESULTS:", results_by_student)

    return render(request, 'teacher-myclass.html', {
        'teacher':            teacher,
        'class_info':         class_info,
        'students':           students,
        'parents':            parents,
        'attendance':         attendance,
        'results_by_student': results_by_student,
    })


@login_required
def class_results_pdf(request):
    teacher = Teacher.objects.get(user=request.user)

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetClassResults @teacher_id = %s",
            [request.user.id]
        )
        rows = cursor.fetchall()

    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_results_{teacher.name}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Class Results Report", styles['Title']))
    elements.append(Paragraph(f"Teacher: {teacher.name}", styles['Normal']))

    # Table data
    data = [['Student', 'Roll No', 'Exam', 'Marks', 'Percentage', 'Result']]
    for r in rows:
        data.append([
            r[1],
            r[2],
            r[3] or '-',
            f"{r[4] or 0}/{r[5] or 0}",
            f"{r[6] or 0}%",
            r[7],
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE',   (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID',       (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


@login_required
def student_result_pdf(request, student_id):
    student = Student.objects.get(id=student_id)

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetStudentExamResults @student_id = %s",
            [student_id]
        )
        rows = cursor.fetchall()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="result_{student.name}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Exam Result Report", styles['Title']))
    elements.append(Paragraph(f"Student: {student.name}", styles['Normal']))
    elements.append(Paragraph(f"Roll No: {student.roll_number}", styles['Normal']))
    elements.append(Paragraph(f"Class: {student.class_name}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))

    # Table
    data = [['Exam', 'Subject', 'Max Marks', 'Obtained', 'Percentage', 'Grade', 'Result']]
    for r in rows:
        data.append([
            r[0],   # exam_name
            r[1],   # subject_name
            r[2],   # max_marks
            r[3],   # obtained_marks
            f"{r[6]}%",  # percentage
            r[4],   # grade
            r[5],   # result
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE',      (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND',    (0,1), (-1,-1), colors.beige),
        ('GRID',          (0,0), (-1,-1), 1, colors.black),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.lightgrey]),
    ]))

    elements.append(table)
    doc.build(elements)
    return response

@login_required
def teacher_profile(request):
    teacher = Teacher.objects.get(user=request.user)

    # Handle profile update
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            teacher.phone = request.POST.get('phone', teacher.phone)
            teacher.alternate_phone = request.POST.get('alternate_phone', teacher.alternate_phone)
            if request.FILES.get('profile_image'):
                teacher.profile_image = request.FILES.get('profile_image')
            teacher.save()
            return redirect('teacher_profile')

        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                return redirect('teacher_profile')

    # Get profile data
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetTeacherProfile @user_id = %s",
            [request.user.id]
        )
        row = cursor.fetchone()
        profile = None
        if row:
            profile = {
                'id':               row[0],
                'name':             row[1],
                'employee_id':      row[2],
                'phone':            row[3],
                'alternate_phone':  row[4],
                'gender':           row[5],
                'date_of_birth':    row[6],
                'department':       row[7],
                'designation':      row[8],
                'joining_date':     row[9],
                'profile_image':    row[10],
                'email':            row[11],
                'class_teacher_of': row[12],
            }

        # Teaching assignments
        cursor.nextset()
        assignment_rows = cursor.fetchall()
        assignments = []
        for r in assignment_rows:
            assignments.append({
                'subject_name': r[0],
                'class_name':   r[1],
                'day_of_week':  r[2],
                'start_time':   r[3],
                'end_time':     r[4],
            })

    return render(request, 'teacher-profile.html', {
        'teacher':     teacher,
        'profile':     profile,
        'assignments': assignments,
    })

@login_required
def teacher_timetable(request):
    teacher = Teacher.objects.get(user=request.user)

    selected_day = request.GET.get('day', None)
    view_type = request.GET.get('view', 'weekly')

    if view_type == 'today':
        selected_day = datetime.now().strftime('%A')

    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_GetTeacherTimetable @user_id = %s, @day_of_week = %s",
            [request.user.id, selected_day]
        )
        rows = cursor.fetchall()

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    today = datetime.now().strftime('%A')

    # Group by day
    timetable = {}
    for day in days_order:
        timetable[day] = []

    for r in rows:
        day = r[3]
        if day in timetable:
            timetable[day].append({
                'id':           r[0],
                'subject_name': r[1],
                'class_name':   r[2],
                'day_of_week':  r[3],
                'start_time':   r[4],
                'end_time':     r[5],
                'status':       r[6],
                'room_number':  r[7],
            })

    if selected_day:
        timetable = {k: v for k, v in timetable.items() if v}

    return render(request, 'teacher-timetable.html', {
        'teacher':      teacher,
        'timetable':    timetable,
        'selected_day': selected_day,
        'view_type':    view_type,
        'today':        today,
        'days':         days_order,
    })

