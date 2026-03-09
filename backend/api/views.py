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


class IsAdminOrOwnerTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        # Teachers can only view/create/delete if it involves their own ID
        if request.user and hasattr(request.user, 'teacher'):
            return True
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if hasattr(request.user, 'teacher') and obj.teacher == request.user.teacher:
            return True
        return False

class TeacherUnavailabilityViewSet(BaseViewSet):
    queryset = TeacherUnavailability.objects.all()
    serializer_class = TeacherUnavailabilitySerializer
    permission_classes = [IsAdminOrOwnerTeacher]

    def get_queryset(self):
        qs = super().get_queryset()
        teacher = self.request.query_params.get('teacher')
        if teacher:
            qs = qs.filter(teacher_id=teacher)
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(teacher__department_id=dept)
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


# --- CONFLICT DETECTION ---
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def detect_conflicts(request, pk):
    """Detect teacher/room/batch conflicts in a timetable."""
    try:
        tt = GeneratedTimetable.objects.get(id=pk)
    except GeneratedTimetable.DoesNotExist:
        return Response({"error": "Timetable not found"}, status=404)

    slots = list(TimetableSlot.objects.filter(timetable=tt).select_related('teacher', 'room', 'batch', 'subject'))
    conflicts = []

    # Group slots by (day, start_time)
    from collections import defaultdict
    by_time = defaultdict(list)
    for s in slots:
        by_time[(s.day, s.start_time.strftime("%H:%M"))].append(s)

    TIME_KEYS = ["07:30", "08:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]

    for (day, time_key), cell_slots in by_time.items():
        slot_idx = TIME_KEYS.index(time_key) if time_key in TIME_KEYS else -1

        # Teacher clash
        teacher_map = defaultdict(list)
        for s in cell_slots:
            teacher_map[s.teacher_id].append(s)
        for tid, slist in teacher_map.items():
            if len(slist) > 1:
                conflicts.append({
                    "type": "teacher",
                    "day": day,
                    "slot_index": slot_idx,
                    "slot_ids": [s.id for s in slist],
                    "detail": f"Teacher '{slist[0].teacher.name}' has {len(slist)} classes at the same time"
                })

        # Room clash
        room_map = defaultdict(list)
        for s in cell_slots:
            room_map[s.room_id].append(s)
        for rid, slist in room_map.items():
            if len(slist) > 1:
                conflicts.append({
                    "type": "room",
                    "day": day,
                    "slot_index": slot_idx,
                    "slot_ids": [s.id for s in slist],
                    "detail": f"Room '{slist[0].room.name}' has {len(slist)} classes at the same time"
                })

        # Batch clash (same batch or parent overlap)
        batch_map = defaultdict(list)
        for s in cell_slots:
            batch_map[s.batch_id].append(s)
            if s.batch.parent_batch_id:
                batch_map[f"parent_{s.batch.parent_batch_id}"].append(s)
        for bid, slist in batch_map.items():
            if isinstance(bid, int) and len(slist) > 1:
                conflicts.append({
                    "type": "batch",
                    "day": day,
                    "slot_index": slot_idx,
                    "slot_ids": [s.id for s in slist],
                    "detail": f"Batch '{slist[0].batch.name}' has {len(slist)} classes at the same time"
                })

    return Response({"conflicts": conflicts})


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


# --- SWAP / MOVE SLOTS ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def swap_slots(request):
    if not request.user.is_staff:
        return Response({"error": "Only admins can swap slots"}, status=403)

    slot_a_id = request.data.get('slot_a_id')
    slot_b_id = request.data.get('slot_b_id')
    slot_id = request.data.get('slot_id')
    target_day = request.data.get('target_day')
    target_slot_index = request.data.get('target_slot_index')

    TIME_SLOT_MAP = {
        0: ("07:30", "08:30"),
        1: ("08:30", "09:30"),
        2: ("10:00", "11:00"),
        3: ("11:00", "12:00"),
        4: ("12:00", "13:00"),
        5: ("13:00", "14:00"),
        6: ("14:00", "15:00"),
        7: ("15:00", "16:00"),
    }

    # --- Case 1: Swap two slots ---
    if slot_a_id and slot_b_id:
        try:
            slot_a = TimetableSlot.objects.get(id=slot_a_id)
            slot_b = TimetableSlot.objects.get(id=slot_b_id)
        except TimetableSlot.DoesNotExist:
            return Response({"error": "Slot not found"}, status=404)

        if slot_a.timetable_id != slot_b.timetable_id:
            return Response({"error": "Slots must belong to the same timetable"}, status=400)

        # Check if either slot is pinned
        time_keys = ["07:30", "08:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
        for s in [slot_a, slot_b]:
            s_time_key = s.start_time.strftime("%H:%M")
            s_idx = time_keys.index(s_time_key) if s_time_key in time_keys else -1
            if PinnedSlot.objects.filter(subject=s.subject, day=s.day, slot_index=s_idx).exists():
                return Response({"error": f"Cannot move '{s.subject.name}' — it is a fixed slot"}, status=400)

        # Swap day, start_time, end_time, room
        slot_a.day, slot_b.day = slot_b.day, slot_a.day
        slot_a.start_time, slot_b.start_time = slot_b.start_time, slot_a.start_time
        slot_a.end_time, slot_b.end_time = slot_b.end_time, slot_a.end_time
        slot_a.room, slot_b.room = slot_b.room, slot_a.room
        slot_a.save()
        slot_b.save()

        return Response({
            "status": "success",
            "slots": [
                TimetableSlotSerializer(slot_a).data,
                TimetableSlotSerializer(slot_b).data,
            ]
        })

    # --- Case 2: Move slot to empty cell ---
    if slot_id and target_day is not None and target_slot_index is not None:
        try:
            slot = TimetableSlot.objects.get(id=slot_id)
        except TimetableSlot.DoesNotExist:
            return Response({"error": "Slot not found"}, status=404)

        # Check if slot is pinned
        time_keys_move = ["07:30", "08:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
        s_time_key = slot.start_time.strftime("%H:%M")
        s_idx = time_keys_move.index(s_time_key) if s_time_key in time_keys_move else -1
        if PinnedSlot.objects.filter(subject=slot.subject, day=slot.day, slot_index=s_idx).exists():
            return Response({"error": f"Cannot move '{slot.subject.name}' — it is a fixed slot"}, status=400)

        idx = int(target_slot_index)
        if idx not in TIME_SLOT_MAP:
            return Response({"error": "Invalid slot index"}, status=400)

        start_str, end_str = TIME_SLOT_MAP[idx]
        from datetime import time as dt_time
        slot.day = target_day
        slot.start_time = dt_time(*map(int, start_str.split(":")))
        slot.end_time = dt_time(*map(int, end_str.split(":")))
        slot.save()

        return Response({
            "status": "success",
            "slots": [TimetableSlotSerializer(slot).data]
        })

    return Response({"error": "Provide either (slot_a_id, slot_b_id) or (slot_id, target_day, target_slot_index)"}, status=400)


# --- PDF EXPORT ---
@csrf_exempt
@api_view(['GET'])
def export_timetable_pdf(request, pk):
    # Accept token from query param since window.open() can't send headers
    token_key = request.query_params.get('token')
    if not token_key:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ', 1)[1]
    if not token_key:
        return Response({"error": "Authentication required. Pass ?token=<your_token>"}, status=401)
    try:
        token_obj = Token.objects.get(key=token_key)
        request.user = token_obj.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=401)
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

    # Clean, readable styles
    cell_style = ParagraphStyle(
        'Cell', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=colors.HexColor('#1e293b'),
        alignment=1  # CENTER
    )
    time_style = ParagraphStyle(
        'TimeCell', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=colors.HexColor('#475569'),
        alignment=1, fontName='Helvetica-Bold'
    )
    header_style = ParagraphStyle(
        'Header', parent=styles['Normal'],
        fontSize=9, leading=11, textColor=colors.white,
        alignment=1, fontName='Helvetica-Bold'
    )
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=16, leading=20, textColor=colors.HexColor('#0f172a'),
        spaceAfter=4, alignment=1
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=colors.HexColor('#64748b'),
        alignment=1
    )

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
    status_label = f"Variant {tt.variant_number}" if tt.status == 'DRAFT' else 'Published'

    title = Paragraph(f"<b>{'  —  '.join(title_parts)}</b>", title_style)
    subtitle = Paragraph(f"{status_label}  •  Generated by ATLAS", subtitle_style)

    header_row = [Paragraph('<b>TIME</b>', header_style)] + [Paragraph(f'<b>{d}</b>', header_style) for d in days]

    data = [header_row]
    for i, row in enumerate(matrix):
        cells = [Paragraph(f'<b>{time_labels[i]}</b>', time_style)]
        for cell_entries in row:
            if cell_entries:
                formatted = []
                for entry in cell_entries:
                    parts = entry.split('\n')
                    subj = f'<b>{parts[0]}</b>' if len(parts) > 0 else ''
                    teacher = f'<br/><i><font color="#475569">{parts[1]}</font></i>' if len(parts) > 1 else ''
                    room = f'<br/><font color="#64748b" size="6">{parts[2]}</font>' if len(parts) > 2 else ''
                    formatted.append(f'{subj}{teacher}{room}')
                cells.append(Paragraph('<br/>'.join(formatted), cell_style))
            else:
                cells.append(Paragraph('<font color="#cbd5e1">—</font>', cell_style))
        data.append(cells)

    col_widths = [80] + [130] * 5
    table = Table(data, colWidths=col_widths)

    # Clean teal header, white body, light alternating rows
    teal = colors.HexColor('#0d9488')
    teal_dark = colors.HexColor('#0f766e')
    light_gray = colors.HexColor('#f8fafc')
    border_color = colors.HexColor('#e2e8f0')

    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), teal),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        # Time column
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f1f5f9')),

        # Alternating row backgrounds
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, light_gray]),

        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, teal_dark),
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.HexColor('#cbd5e1')),

        # Alignment and padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements = [title, subtitle, Spacer(1, 14), table]
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="timetable_{pk}.pdf"'
    return response
