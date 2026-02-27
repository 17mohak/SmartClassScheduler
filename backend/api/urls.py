from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, TeacherViewSet, SubjectViewSet,
    StudentBatchViewSet, DepartmentViewSet,
    GeneratedTimetableViewSet, TimetableSlotViewSet,
    PinnedSlotViewSet,
    trigger_generation, approve_timetable, export_timetable_pdf
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

urlpatterns = [
    path('', include(router.urls)),
    path('generate/', trigger_generation, name='generate-timetable'),
    path('timetables/<int:pk>/approve/', approve_timetable, name='approve-timetable'),
    path('timetables/<int:pk>/pdf/', export_timetable_pdf, name='export-timetable-pdf'),
]