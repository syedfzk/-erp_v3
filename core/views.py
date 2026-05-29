from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import connection
from datetime import datetime, date, timedelta
from .models import Student,HomeworkSubmission,FeeAssignment,FeePayment,FeeType,Exam, ExamSchedule, ExamResult
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, date, timedelta
from django.views.decorators.http import require_POST




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

def login_view(request):
    if request.user.is_authenticated:
        try:
            Student.objects.get(user=request.user)
            return redirect('student_dashboard')
        except Student.DoesNotExist:
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