from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, TeacherViewSet, SubjectViewSet,
    StudentBatchViewSet, DepartmentViewSet,
    GeneratedTimetableViewSet, TimetableSlotViewSet
)

# This router automatically creates URLs like /api/teachers/, /api/rooms/, etc.
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
]