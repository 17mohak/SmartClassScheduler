from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .serializers import *
from .scheduler import generate_timetable


# --- AUTHENTICATION API ---

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)

        # Determine Role
        is_admin = user.is_staff
        teacher_id = None
        dept_id = None

        if not is_admin:
            # If not admin, find which Teacher profile they are linked to
            try:
                teacher = Teacher.objects.get(user=user)
                teacher_id = teacher.id
                dept_id = teacher.department.id
            except Teacher.DoesNotExist:
                return Response({"error": "User is not linked to a Teacher profile"}, status=400)

        return Response({
            "token": token.key,
            "is_admin": is_admin,
            "teacher_id": teacher_id,
            "department_id": dept_id,
            "username": user.username
        })
    else:
        return Response({"error": "Invalid Credentials"}, status=400)


# --- PROTECTED VIEWSETS ---
# Only Admin can write (create/delete/update). Others can only read.

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET is safe
            return True
        return request.user and request.user.is_staff  # Only Admin can POST/PUT/DELETE


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Default protection


class TeacherViewSet(BaseViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only Admin adds teachers


class SubjectViewSet(BaseViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only Admin adds subjects


# ... (Apply similar logic to Department, Room, StudentBatch) ...
class DepartmentViewSet(BaseViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]


class RoomViewSet(BaseViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]


class StudentBatchViewSet(BaseViewSet):
    queryset = StudentBatch.objects.all()
    serializer_class = StudentBatchSerializer
    permission_classes = [IsAdminOrReadOnly]


class GeneratedTimetableViewSet(viewsets.ModelViewSet):
    queryset = GeneratedTimetable.objects.all()
    serializer_class = GeneratedTimetableSerializer


class TimetableSlotViewSet(viewsets.ModelViewSet):
    queryset = TimetableSlot.objects.all()
    serializer_class = TimetableSlotSerializer


# --- GENERATION TRIGGER ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])  # Must be logged in
def trigger_generation(request):
    department_id = request.data.get('department_id')

    # Security Check: Faculty can only generate for their OWN department
    if not request.user.is_staff:
        try:
            teacher = Teacher.objects.get(user=request.user)
            if str(teacher.department.id) != str(department_id):
                return Response({"error": "You can only manage your own department"}, status=403)
        except Teacher.DoesNotExist:
            return Response({"error": "Unauthorized"}, status=403)

    result = generate_timetable(department_id)
    return Response({"status": "Success", "message": result})