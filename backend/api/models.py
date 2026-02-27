from django.db import models
from django.contrib.auth.models import User


# 1. Department (No dependencies)
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self): return self.name


# 2. StudentBatch (Depends on Department)
class StudentBatch(models.Model):
    name = models.CharField(max_length=100)
    size = models.IntegerField(default=60)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    parent_batch = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_batches')
    max_classes_per_day = models.IntegerField(default=6)

    def __str__(self): return self.name


# 3. Teacher (Depends on Department & User)
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    preferred_start_slot = models.IntegerField(default=0)
    preferred_end_slot = models.IntegerField(default=8)
    max_classes_per_day = models.IntegerField(default=4)

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


# 6. PinnedSlot (Fixed/special class slots)
class PinnedSlot(models.Model):
    DAY_CHOICES = [('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday')]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='pinned_slots')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    slot_index = models.IntegerField(help_text="0-7 corresponding to time slots")

    class Meta:
        unique_together = ('subject', 'day', 'slot_index')

    def __str__(self): return f"{self.subject.name} pinned to {self.day} slot {self.slot_index}"


# 7. GeneratedTimetable (Depends on Department)
class GeneratedTimetable(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('PUBLISHED', 'Published')]
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    variant_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.department.name} - Variant {self.variant_number} ({self.status})"


# 8. TimetableSlot (Depends on everything)
class TimetableSlot(models.Model):
    timetable = models.ForeignKey(GeneratedTimetable, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=3)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE)