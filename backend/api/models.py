from django.db import models


# 1. Department (To support "Multi-department" requirement)
class Department(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Computer Science", "Electronics"

    def __str__(self):
        return self.name


# 2. Room (Matches "Number of classrooms available" & "Room capacity")
class Room(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.IntegerField()
    is_lab = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({'Lab' if self.is_lab else 'Theory'})"


# 3. Teacher (Matches "Avg leaves" & "Workload norms")
class Teacher(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)

    # Specific Parameter: "Average number of leaves a faculty member takes in a month"
    avg_leaves_per_month = models.IntegerField(default=0)

    # Specific Parameter: "Max classes per day/week" (Workload distribution)
    max_lectures_per_week = models.IntegerField(default=15)

    def __str__(self):
        return self.name


# 4. Subject (Matches "Names of subjects" & "Classes per week")
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_practical = models.BooleanField(default=False)

    # Parameter: "Number of classes to be conducted for a subject per week"
    weekly_lectures = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.code})"


# 5. Student Batch (Matches "Number of batches" & "Multi-shift")
class StudentBatch(models.Model):
    name = models.CharField(max_length=50)  # e.g., "CSE - Sem 6"
    size = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    # Parameter: "Support for multi-shift scheduling"
    SHIFT_CHOICES = (('M', 'Morning'), ('E', 'Evening'))
    shift = models.CharField(max_length=1, choices=SHIFT_CHOICES, default='M')

    def __str__(self):
        return self.name


# 6. Timetable Wrapper (Matches "Multiple options" & "Approval workflow")
class GeneratedTimetable(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PROPOSED', 'Proposed for Review'),  # For "Competent Authorities"
        ('APPROVED', 'Approved'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Timetable for {self.department} ({self.status})"


# 7. The Actual Slot (Matches "Fixed slots" & "Optimized assignments")
class TimetableSlot(models.Model):
    DAYS_OF_WEEK = (
        ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
        ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'),
    )

    timetable = models.ForeignKey(GeneratedTimetable, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE)

    # Specific Parameter: "Special classes that have fixed slots"
    # If True, the algorithm will NOT move this slot.
    is_fixed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.day} {self.start_time}: {self.subject}"