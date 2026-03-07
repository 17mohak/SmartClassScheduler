from django.contrib import admin
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot, PinnedSlot, LeaveApplication


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_lab')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'email', 'max_classes_per_day')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'batch', 'teacher')

@admin.register(StudentBatch)
class StudentBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'department', 'max_classes_per_day')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(GeneratedTimetable)
class GeneratedTimetableAdmin(admin.ModelAdmin):
    list_display = ('department', 'variant_number', 'status', 'created_at')

@admin.register(PinnedSlot)
class PinnedSlotAdmin(admin.ModelAdmin):
    list_display = ('subject', 'department', 'day', 'slot_index')

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day', 'slot_index', 'status', 'created_at')
    list_filter = ('status', 'day')
    search_fields = ('teacher__name', 'reason')

admin.site.register(TimetableSlot)