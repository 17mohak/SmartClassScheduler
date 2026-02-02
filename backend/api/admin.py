from django.contrib import admin
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot

# Notice: We inherit from (admin.ModelAdmin), NOT (admin.register...)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_lab')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'email')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department')

@admin.register(StudentBatch)
class StudentBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'department')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(GeneratedTimetable)
class GeneratedTimetableAdmin(admin.ModelAdmin):
    list_display = ('department', 'status', 'created_at')

admin.site.register(TimetableSlot)