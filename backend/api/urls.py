from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, TeacherViewSet, SubjectViewSet,
    StudentBatchViewSet, DepartmentViewSet,
    GeneratedTimetableViewSet, TimetableSlotViewSet,
    trigger_generation # <--- Import the new view function
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'batches', StudentBatchViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'timetables', GeneratedTimetableViewSet)
router.register(r'slots', TimetableSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # This creates the new link: http://127.0.0.1:8000/api/generate/
    path('generate/', trigger_generation, name='generate-timetable'),
]