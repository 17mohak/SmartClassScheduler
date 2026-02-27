from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import *
from .serializers import *
from .scheduler import generate_timetable

import io


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

        is_admin = user.is_staff
        teacher_id = None
        dept_id = None
        teacher_name = None

        if not is_admin:
            try:
                teacher = Teacher.objects.get(user=user)
                teacher_id = teacher.id
                dept_id = teacher.department.id
                teacher_name = teacher.name
            except Teacher.DoesNotExist:
                return Response({"error": "User is not linked to a Teacher profile"}, status=400)

        return Response({
            "token": token.key,
            "is_admin": is_admin,
            "teacher_id": teacher_id,
            "department_id": dept_id,
            "username": user.username,
            "teacher_name": teacher_name
        })
    else:
        return Response({"error": "Invalid Credentials"}, status=400)


# --- PERMISSIONS ---

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TeacherViewSet(BaseViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOrReadOnly]


class SubjectViewSet(BaseViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]


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


class PinnedSlotViewSet(BaseViewSet):
    queryset = PinnedSlot.objects.all()
    serializer_class = PinnedSlotSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs


class GeneratedTimetableViewSet(viewsets.ModelViewSet):
    queryset = GeneratedTimetable.objects.all()
    serializer_class = GeneratedTimetableSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        # Faculty can only see PUBLISHED timetables
        if self.request.user and not self.request.user.is_staff:
            qs = qs.filter(status='PUBLISHED')
        return qs


class TimetableSlotViewSet(viewsets.ModelViewSet):
    queryset = TimetableSlot.objects.all()
    serializer_class = TimetableSlotSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(timetable__department_id=dept)

        # Faculty: only see PUBLISHED timetable slots
        if self.request.user and not self.request.user.is_staff:
            qs = qs.filter(timetable__status='PUBLISHED')

        timetable = self.request.query_params.get('timetable')
        if timetable:
            qs = qs.filter(timetable_id=timetable)

        batch = self.request.query_params.get('batch')
        if batch:
            from .models import StudentBatch
            sub_ids = list(StudentBatch.objects.filter(parent_batch_id=batch).values_list('id', flat=True))
            all_ids = [int(batch)] + sub_ids
            qs = qs.filter(batch_id__in=all_ids)

        teacher = self.request.query_params.get('teacher')
        if teacher:
            qs = qs.filter(teacher_id=teacher)
        return qs


# --- GENERATION TRIGGER ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_generation(request):
    department_id = request.data.get('department_id')

    if not request.user.is_staff:
        try:
            teacher = Teacher.objects.get(user=request.user)
            if str(teacher.department.id) != str(department_id):
                return Response({"error": "You can only manage your own department"}, status=403)
        except Teacher.DoesNotExist:
            return Response({"error": "Unauthorized"}, status=403)

    try:
        result = generate_timetable(department_id)
    except Exception as e:
        return Response({"error": f"Scheduler error: {str(e)}"}, status=500)

    if result['status'] == 'error':
        return Response({"error": result['messages'][0]}, status=400)

    return Response(result)


# --- APPROVE TIMETABLE ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_timetable(request, pk):
    if not request.user.is_staff:
        return Response({"error": "Only admins can approve timetables"}, status=403)

    try:
        tt = GeneratedTimetable.objects.get(id=pk)
    except GeneratedTimetable.DoesNotExist:
        return Response({"error": "Timetable not found"}, status=404)

    # Delete all other timetables for this department (DRAFTs and old PUBLISHED)
    GeneratedTimetable.objects.filter(department=tt.department).exclude(id=pk).delete()

    tt.status = 'PUBLISHED'
    tt.save()

    return Response({"status": "success", "message": f"Variant {tt.variant_number} published! All other variants deleted."})


# --- PDF EXPORT ---
@csrf_exempt
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_timetable_pdf(request, pk):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        return Response({"error": "reportlab is not installed. Run: pip install reportlab"}, status=500)

    try:
        tt = GeneratedTimetable.objects.get(id=pk)
    except GeneratedTimetable.DoesNotExist:
        return Response({"error": "Timetable not found"}, status=404)

    batch_id = request.query_params.get('batch')
    teacher_id = request.query_params.get('teacher')

    slots = TimetableSlot.objects.filter(timetable=tt)
    if batch_id:
        sub_ids = list(StudentBatch.objects.filter(parent_batch_id=batch_id).values_list('id', flat=True))
        all_ids = [int(batch_id)] + sub_ids
        slots = slots.filter(batch_id__in=all_ids)
    if teacher_id:
        slots = slots.filter(teacher_id=teacher_id)

    slots = slots.select_related('subject', 'teacher', 'room', 'batch')

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    time_labels = [
        "07:30-08:30", "08:30-09:30", "10:00-11:00", "11:00-12:00",
        "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00"
    ]
    time_keys = ["07:30", "08:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]

    matrix = [[[] for _ in range(5)] for _ in range(8)]
    for slot in slots:
        time_key = slot.start_time.strftime("%H:%M")
        try:
            row = time_keys.index(time_key)
        except ValueError:
            continue
        try:
            col = days.index(slot.day)
        except ValueError:
            continue
        matrix[row][col].append(f"{slot.subject.name}\n{slot.teacher.name}\n{slot.room.name}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7, leading=9)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.white)

    # Determine title
    title_parts = [tt.department.name]
    if batch_id:
        batch_obj = StudentBatch.objects.filter(id=batch_id).first()
        if batch_obj:
            title_parts.append(batch_obj.name)
    if teacher_id:
        teacher_obj = Teacher.objects.filter(id=teacher_id).first()
        if teacher_obj:
            title_parts.append(teacher_obj.name)
    title_parts.append(f"Variant {tt.variant_number}" if tt.status == 'DRAFT' else 'Published')

    title = Paragraph(f"<b>{'  —  '.join(title_parts)}</b>", styles['Title'])

    header_row = [Paragraph('<b>Time</b>', header_style)] + [Paragraph(f'<b>{d}</b>', header_style) for d in days]

    data = [header_row]
    for i, row in enumerate(matrix):
        cells = [Paragraph(f'<b>{time_labels[i]}</b>', cell_style)]
        for cell_entries in row:
            if cell_entries:
                cells.append(Paragraph('<br/>---<br/>'.join(cell_entries), cell_style))
            else:
                cells.append('')
        data.append(cells)

    col_widths = [80] + [130] * 5
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#94a3b8')),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.HexColor('#0f172a'), colors.HexColor('#1e293b')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements = [title, Spacer(1, 12), table]
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="timetable_{pk}.pdf"'
    return response
