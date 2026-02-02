from rest_framework import viewsets
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot
from .serializers import (
    RoomSerializer, TeacherSerializer, SubjectSerializer,
    StudentBatchSerializer, DepartmentSerializer,
    GeneratedTimetableSerializer, TimetableSlotSerializer
)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class StudentBatchViewSet(viewsets.ModelViewSet):
    queryset = StudentBatch.objects.all()
    serializer_class = StudentBatchSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class GeneratedTimetableViewSet(viewsets.ModelViewSet):
    queryset = GeneratedTimetable.objects.all()
    serializer_class = GeneratedTimetableSerializer

class TimetableSlotViewSet(viewsets.ModelViewSet):
    queryset = TimetableSlot.objects.all()
    serializer_class = TimetableSlotSerializer