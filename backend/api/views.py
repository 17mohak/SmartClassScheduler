from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot
from .serializers import (
    RoomSerializer, TeacherSerializer, SubjectSerializer,
    StudentBatchSerializer, DepartmentSerializer,
    GeneratedTimetableSerializer, TimetableSlotSerializer
)
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

# --- THE NUCLEAR FIX ---
@csrf_exempt
@api_view(['POST'])
@authentication_classes([]) # <--- NEW: Tells Django to ignore your Admin login
@permission_classes([AllowAny])
def trigger_generation(request):
    department_id = request.data.get('department_id')
    result = generate_timetable(department_id)
    return Response({"status": "Success", "message": result})