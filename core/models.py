from django.db import models
from django.contrib.auth.models import User
from django.conf import settings  

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    class_name = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to='student_images/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    result_status = models.CharField(max_length=10, choices=[
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
        ('Pending', 'Pending')
    ], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class ClassSchedule(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress'),
        ('Upcoming', 'Upcoming'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Upcoming')

    def __str__(self):
        return f"{self.subject.name} - {self.class_name}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present',  'Present'),
        ('Absent',   'Absent'),
        ('Half-Day', 'Half-Day'),
    ]
    student    = models.ForeignKey(Student, on_delete=models.CASCADE)
    date       = models.DateField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    marked_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"
    
class Exam(models.Model):
    name = models.CharField(max_length=100)  # e.g. "1st Quarterly"
    class_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.exam.name} - {self.subject.name}"
    
class ExamResult(models.Model):
    GRADE_CHOICES = [
        ('O', 'Outstanding'),
        ('A+', 'Excellent'),
        ('A', 'Very Good'),
        ('B+', 'Good'),
        ('B', 'Above Average'),
        ('C', 'Average'),
        ('F', 'Fail'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    max_marks = models.IntegerField(default=100)
    obtained_marks = models.IntegerField()
    grade = models.CharField(max_length=5, choices=GRADE_CHOICES)
    result = models.CharField(max_length=10, choices=[
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
    ])

    class Meta:
        unique_together = ('student', 'exam', 'subject')

    def __str__(self):
        return f"{self.student.name} - {self.exam.name} - {self.subject.name}"
    
class Homework(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    attachment = models.FileField(upload_to='homework/', blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.class_name}"


class HomeworkSubmission(models.Model):
    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Late', 'Late'),
        ('Reviewed', 'Reviewed'),
    ]
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    teacher_remarks = models.TextField(blank=True, null=True)
    marks = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ('homework', 'student')

    def __str__(self):
        return f"{self.student.name} - {self.homework.title}"

class FeeType(models.Model):
    name = models.CharField(max_length=100)   # Tuition Fee, Transport Fee, etc.
    description = models.TextField(blank=True, null=True)
 
    def __str__(self):
        return self.name
 
 
class FeeAssignment(models.Model):
    """One row per student per fee type per term/month."""
    TERM_CHOICES = [
        ('April',     'April'),
        ('May',       'May'),
        ('June',      'June'),
        ('July',      'July'),
        ('August',    'August'),
        ('September', 'September'),
        ('October',   'October'),
        ('November',  'November'),
        ('December',  'December'),
        ('January',   'January'),
        ('February',  'February'),
        ('March',     'March'),
        # Term-based alternatives:
        ('Term 1',    'Term 1'),
        ('Term 2',    'Term 2'),
        ('Term 3',    'Term 3'),
        ('Annual',    'Annual'),
    ]
    STATUS_CHOICES = [
        ('Paid',     'Paid'),
        ('Pending',  'Pending'),
        ('Overdue',  'Overdue'),
    ]
 
    student      = models.ForeignKey(Student,   on_delete=models.CASCADE)
    fee_type     = models.ForeignKey(FeeType,   on_delete=models.CASCADE)
    term         = models.CharField(max_length=20, choices=TERM_CHOICES)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    due_date     = models.DateField()
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    discount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    academic_year = models.CharField(max_length=10, default='2024-25')  # e.g. 2024-25
    created_at   = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        unique_together = ('student', 'fee_type', 'term', 'academic_year')
 
    def __str__(self):
        return f"{self.student.name} - {self.fee_type.name} - {self.term}"
 
    @property
    def net_amount(self):
        return self.amount - self.discount + self.fine
 
 
class FeePayment(models.Model):
    """One row per actual payment transaction."""
    METHOD_CHOICES = [
        ('Cash',          'Cash'),
        ('Online',        'Online'),
        ('Cheque',        'Cheque'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI',           'UPI'),
    ]
 
    assignment     = models.ForeignKey(FeeAssignment, on_delete=models.CASCADE,
                                       related_name='payments')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid    = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    remarks        = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.assignment.student.name}"
 

class Notice(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    TARGET_CHOICES = [
        ('all', 'All Students'),
        ('class', 'Specific Class'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    target_class = models.CharField(max_length=50, blank=True, null=True)  # e.g. '5th'
    published_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        ordering = ['-published_date', '-id']

    def __str__(self):
        return self.title
    
class Event(models.Model):
    CATEGORY_CHOICES = [
        ('academic',     'Academic'),
        ('sports',       'Sports'),
        ('cultural',     'Cultural'),
        ('holiday',      'Holiday'),
        ('exam',         'Exam'),
        ('other',        'Other'),
    ]
    TARGET_CHOICES = [
        ('all',   'All Students'),
        ('class', 'Specific Class'),
    ]

    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    target      = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    target_class= models.CharField(max_length=50, blank=True, null=True)
    event_date  = models.DateField()
    end_date    = models.DateField(blank=True, null=True)   # for multi-day events
    start_time  = models.TimeField(blank=True, null=True)
    end_time    = models.TimeField(blank=True, null=True)
    venue       = models.CharField(max_length=255, blank=True)
    is_active   = models.BooleanField(default=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return f"{self.title} ({self.event_date})"
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)  # NEW
    gender = models.CharField(max_length=10, choices=[                         # NEW
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ], blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)                   # NEW
    department = models.CharField(max_length=100, blank=True, null=True)      # NEW
    designation = models.CharField(max_length=100, blank=True, null=True)     # NEW
    profile_image = models.ImageField(upload_to='teacher_images/', blank=True, null=True)
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class TeacherAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present',  'Present'),
        ('Absent',   'Absent'),
        ('Late',     'Late'),
        ('Half Day', 'Half Day'),
        ('Holiday',  'Holiday'),
    ]
    teacher    = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date       = models.DateField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks    = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.teacher.name} - {self.date} - {self.status}"
    
class ClassTeacher(models.Model):
    teacher    = models.OneToOneField(Teacher, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher.name} → Class {self.class_name}"
    
class Parent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parents')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=20, choices=[
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Guardian', 'Guardian'),
    ])
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.relation}) - {self.student.name}"
    
class TeacherSchedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress'),
        ('Upcoming', 'Upcoming'),
    ]
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Upcoming')

    def __str__(self):
        return f"{self.teacher.name} - {self.subject.name} - {self.class_name} - {self.day_of_week}"