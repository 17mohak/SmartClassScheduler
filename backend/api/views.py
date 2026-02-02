from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot
from .serializers import (
    RoomSerializer, TeacherSerializer, SubjectSerializer,
    StudentBatchSerializer, DepartmentSerializer,
    GeneratedTimetableSerializer, TimetableSlotSerializer
)
# We import the scheduler here
from .scheduler import generate_timetable

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

# --- FIX IS HERE: This function must be OUTSIDE the classes ---

@api_view(['POST'])
def trigger_generation(request):
    department_id = request.data.get('department_id')
    # Call the algorithm
    result = generate_timetable(department_id)
    return Response({"status": "Success", "message": result})