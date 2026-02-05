from ortools.sat.python import cp_model
from .models import Room, Teacher, Subject, StudentBatch, TimetableSlot, GeneratedTimetable, Department


def generate_timetable(department_id):
    model = cp_model.CpModel()

    # 1. Fetch Data
    batches = list(StudentBatch.objects.filter(department_id=department_id))
    subjects = list(Subject.objects.filter(department_id=department_id))
    teachers = list(Teacher.objects.filter(department_id=department_id))
    rooms = list(Room.objects.all())

    if not teachers or not subjects or not batches:
        return "Error: Missing data. Need Teachers, Subjects, and Batches."

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']

    # --- CUSTOM TIME MAPPING ---
    # Slot 0: 07:30 - 08:30
    # Slot 1: 08:30 - 09:30
    # -- BREAK (30 mins) --
    # Slot 2: 10:00 - 11:00
    # Slot 3: 11:00 - 12:00
    # Slot 4: 12:00 - 13:00
    # Slot 5: 13:00 - 14:00
    # Slot 6: 14:00 - 15:00
    # Slot 7: 15:00 - 16:00

    time_slots = [
        "07:30", "08:30",  # Pre-break
        "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"  # Post-break
    ]
    slots_per_day = len(time_slots)  # 8 Slots

    # 2. Create Variables
    # shifts[(t, s, b, r, day, slot)] = bool
    shifts = {}

    for s in subjects:
        target_batch = s.batch
        if not target_batch: continue

        t = s.teacher
        if not t: continue

        for r in rooms:
            if target_batch.size > r.capacity: continue

            for day in days:
                for slot in range(slots_per_day):
                    # Check Teacher Preferences (0-7 integer comparison)
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot:
                        continue

                    key = (t.id, s.id, target_batch.id, r.id, day, slot)
                    shifts[key] = model.NewBoolVar(f'shift_{key}')

    # 3. Add Hard Constraints

    # C1: Weekly Lectures
    for s in subjects:
        if not s.batch or not s.teacher: continue
        candidates = []
        for r in rooms:
            if s.batch.size > r.capacity: continue
            for day in days:
                for slot in range(slots_per_day):
                    t = s.teacher
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot: continue
                    key = (t.id, s.id, s.batch.id, r.id, day, slot)
                    if key in shifts: candidates.append(shifts[key])
        if candidates:
            model.Add(sum(candidates) == s.weekly_lectures)

    # C2: Teacher Conflict
    for t in teachers:
        for day in days:
            for slot in range(slots_per_day):
                moves = [var for k, var in shifts.items() if k[0] == t.id and k[4] == day and k[5] == slot]
                if moves: model.Add(sum(moves) <= 1)

    # C3: Room Conflict
    for r in rooms:
        for day in days:
            for slot in range(slots_per_day):
                moves = [var for k, var in shifts.items() if k[3] == r.id and k[4] == day and k[5] == slot]
                if moves: model.Add(sum(moves) <= 1)

    # C4: Batch Conflict
    for b in batches:
        for day in days:
            for slot in range(slots_per_day):
                moves = [var for k, var in shifts.items() if k[2] == b.id and k[4] == day and k[5] == slot]
                if moves: model.Add(sum(moves) <= 1)

    # 4. Solve and Save
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        dept = Department.objects.get(id=department_id)
        # Wipe old draft
        GeneratedTimetable.objects.filter(department=dept).delete()

        new_tt = GeneratedTimetable.objects.create(department=dept, status="FINAL")

        count = 0
        for key, var in shifts.items():
            if solver.Value(var) == 1:
                t_id, s_id, b_id, r_id, day, slot_num = key

                # --- CALCULATE TIME STRINGS ---
                start_str = time_slots[slot_num]

                # Handle End Time
                if slot_num == 1:
                    # Special Case: Slot 1 (8:30) ends at 9:30 for break
                    end_str = "09:30"
                else:
                    # Standard Case: 1 Hour duration
                    # Parse "HH:MM", add 1 to HH
                    h, m = map(int, start_str.split(':'))
                    end_str = f"{h + 1:02d}:{m:02d}"

                TimetableSlot.objects.create(
                    timetable=new_tt,
                    day=day,
                    start_time=start_str,
                    end_time=end_str,
                    room_id=r_id,
                    teacher_id=t_id,
                    subject_id=s_id,
                    batch_id=b_id
                )
                count += 1
        return f"Success! Created {count} slots."

    return "Conflict! Unable to satisfy all constraints. Try adding rooms or relaxing preferences."