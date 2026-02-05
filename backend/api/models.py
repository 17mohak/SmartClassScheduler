from django.db import models
from django.contrib.auth.models import User


# 1. Department (No dependencies)
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self): return self.name


# 2. StudentBatch (Depends on Department)
class StudentBatch(models.Model):
    name = models.CharField(max_length=100)  # e.g., "FY Computer Science"
    size = models.IntegerField(default=60)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self): return self.name


# 3. Teacher (Depends on Department & User)
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    preferred_start_slot = models.IntegerField(default=0)
    preferred_end_slot = models.IntegerField(default=7)

    def __str__(self): return self.name


# 4. Subject (Depends on Department, Batch, Teacher)
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    weekly_lectures = models.IntegerField(default=3)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.batch.name if self.batch else 'General'})"


# 5. Room (No dependencies)
class Room(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.IntegerField(default=60)
    is_lab = models.BooleanField(default=False)

    def __str__(self): return self.name


# 6. GeneratedTimetable (Depends on Department)
class GeneratedTimetable(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)


# 7. TimetableSlot (Depends on everything)
class TimetableSlot(models.Model):
    timetable = models.ForeignKey(GeneratedTimetable, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=3)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE)