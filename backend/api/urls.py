from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, TeacherViewSet, SubjectViewSet,
    StudentBatchViewSet, DepartmentViewSet,
    GeneratedTimetableViewSet, TimetableSlotViewSet,
    PinnedSlotViewSet, TeacherUnavailabilityViewSet,
    trigger_generation, approve_timetable, export_timetable_pdf, swap_slots,
    detect_conflicts
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'batches', StudentBatchViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'timetables', GeneratedTimetableViewSet)
router.register(r'slots', TimetableSlotViewSet)
router.register(r'pinned-slots', PinnedSlotViewSet)
router.register(r'teacher-unavailability', TeacherUnavailabilityViewSet)

urlpatterns = [
    path('slots/swap/', swap_slots, name='swap-slots'),
    path('generate/', trigger_generation, name='generate-timetable'),
    path('timetables/<int:pk>/approve/', approve_timetable, name='approve-timetable'),
    path('timetables/<int:pk>/pdf/', export_timetable_pdf, name='export-timetable-pdf'),
    path('timetables/<int:pk>/conflicts/', detect_conflicts, name='detect-conflicts'),
    path('', include(router.urls)),
]