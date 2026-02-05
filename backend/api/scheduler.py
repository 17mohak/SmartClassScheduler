from ortools.sat.python import cp_model
from .models import Room, Teacher, Subject, StudentBatch, TimetableSlot, GeneratedTimetable, Department


def generate_timetable(department_id):
    model = cp_model.CpModel()

    # 1. Fetch Data
    # Fetch batches only for this department
    batches = list(StudentBatch.objects.filter(department_id=department_id))
    # Fetch subjects only for these batches
    subjects = list(Subject.objects.filter(department_id=department_id))
    teachers = list(Teacher.objects.filter(department_id=department_id))
    rooms = list(Room.objects.all())

    if not teachers or not subjects or not batches:
        return "Error: Missing data. Need Teachers, Subjects, and Batches."

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    slots_per_day = 8  # 9 AM to 5 PM

    # 2. Create Variables
    shifts = {}

    for s in subjects:
        # CRITICAL: Only schedule this subject for its assigned batch!
        # If subject.batch is None, we skip it (or assign to all, but let's be strict)
        target_batch = s.batch
        if not target_batch:
            continue

            # Assigned Teacher (from DB)
        t = s.teacher
        if not t:
            continue  # Skip subjects with no teacher assigned

        for r in rooms:
            # Capacity Check
            if target_batch.size > r.capacity:
                continue

            for day in days:
                for slot in range(slots_per_day):
                    # --- NEW CONSTRAINT: TEACHER PREFERENCES ---
                    # If this slot is outside the teacher's preferred hours, SKIP IT.
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot:
                        continue
                        # -------------------------------------------

                    key = (t.id, s.id, target_batch.id, r.id, day, slot)
                    shifts[key] = model.NewBoolVar(f'shift_{key}')

    # 3. Add Hard Constraints

    # C1: Weekly Lectures (Must happen X times)
    for s in subjects:
        if not s.batch or not s.teacher: continue

        candidates = []
        for r in rooms:
            if s.batch.size > r.capacity: continue
            for day in days:
                for slot in range(slots_per_day):
                    t = s.teacher
                    # Check preferences again to ensure we access valid keys
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot:
                        continue

                    key = (t.id, s.id, s.batch.id, r.id, day, slot)
                    if key in shifts:
                        candidates.append(shifts[key])

        if candidates:
            model.Add(sum(candidates) == s.weekly_lectures)

    # C2: No Overlap - Teacher
    for t in teachers:
        for day in days:
            for slot in range(slots_per_day):
                # Gather all simultaneous classes for this teacher
                moves = [var for k, var in shifts.items() if k[0] == t.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # C3: No Overlap - Room
    for r in rooms:
        for day in days:
            for slot in range(slots_per_day):
                moves = [var for k, var in shifts.items() if k[3] == r.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # C4: No Overlap - Batch
    for b in batches:
        for day in days:
            for slot in range(slots_per_day):
                moves = [var for k, var in shifts.items() if k[2] == b.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # 4. Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        dept = Department.objects.get(id=department_id)
        # Clear old drafts for cleanliness (Optional)
        # GeneratedTimetable.objects.filter(department=dept, status="DRAFT").delete()

        new_tt = GeneratedTimetable.objects.create(department=dept, status="FINAL")

        count = 0
        for key, var in shifts.items():
            if solver.Value(var) == 1:
                t_id, s_id, b_id, r_id, day, slot_num = key
                start_hour = 9 + slot_num

                TimetableSlot.objects.create(
                    timetable=new_tt,
                    day=day,
                    start_time=f"{start_hour:02d}:00",
                    end_time=f"{start_hour + 1:02d}:00",
                    room_id=r_id,
                    teacher_id=t_id,
                    subject_id=s_id,
                    batch_id=b_id
                )
                count += 1
        return f"Success! Created {count} slots for {len(batches)} batches."

    return "Conflict! No schedule possible. Try relaxing teacher hours or adding rooms."