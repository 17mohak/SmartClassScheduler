from ortools.sat.python import cp_model
from .models import Room, Teacher, Subject, StudentBatch, TimetableSlot, GeneratedTimetable, Department


def generate_timetable(department_id):
    # --- 1. SETUP & DATA FETCHING ---
    model = cp_model.CpModel()

    # Fetch all resources for this department
    teachers = list(Teacher.objects.filter(department_id=department_id))
    rooms = list(Room.objects.all())  # Assume rooms are shared or just use all
    subjects = list(Subject.objects.filter(department_id=department_id))
    batches = list(StudentBatch.objects.filter(department_id=department_id))

    if not teachers or not subjects or not batches:
        return "Error: Missing data. Need Teachers, Subjects, and Batches."

    # Define Dimensions
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    slots_per_day = 6  # E.g., 9am-4pm
    all_slots = range(len(days) * slots_per_day)  # 0 to 29

    # --- 2. CREATE VARIABLES ---
    # shifts[(t, s, b, r, day, slot)] = 1 if class is scheduled, else 0
    shifts = {}

    for t in teachers:
        for s in subjects:
            for b in batches:
                # Basic check: Does this teacher teach this subject? (Simplified: Yes)
                # Does this batch take this subject? (Simplified: Yes)
                for r in rooms:
                    for d_idx, day in enumerate(days):
                        for slot in range(slots_per_day):
                            key = (t.id, s.id, b.id, r.id, day, slot)
                            shifts[key] = model.NewBoolVar(f'shift_{key}')

    # --- 3. HARD CONSTRAINTS ---

    # C1: Each class (Subject + Batch) must be taught exactly X times a week.
    # (For simplicity, we assume every Subject-Batch pair needs 'weekly_lectures')
    for s in subjects:
        for b in batches:
            # Gather all possible slots/rooms/teachers for this specific subject-batch
            candidates = []
            for t in teachers:
                for r in rooms:
                    for d_idx, day in enumerate(days):
                        for slot in range(slots_per_day):
                            key = (t.id, s.id, b.id, r.id, day, slot)
                            if key in shifts:
                                candidates.append(shifts[key])

            # Sum of all occurrences must equal weekly_lectures (e.g., 3)
            if candidates:
                model.Add(sum(candidates) == s.weekly_lectures)

    # C2: No Teacher can be in two places at once
    for t in teachers:
        for d_idx, day in enumerate(days):
            for slot in range(slots_per_day):
                # Sum of all classes this teacher teaches in this specific slot <= 1
                teacher_moves = []
                for s in subjects:
                    for b in batches:
                        for r in rooms:
                            key = (t.id, s.id, b.id, r.id, day, slot)
                            if key in shifts:
                                teacher_moves.append(shifts[key])
                model.Add(sum(teacher_moves) <= 1)

    # C3: No Room can host two classes at once
    for r in rooms:
        for d_idx, day in enumerate(days):
            for slot in range(slots_per_day):
                room_moves = []
                for t in teachers:
                    for s in subjects:
                        for b in batches:
                            key = (t.id, s.id, b.id, r.id, day, slot)
                            if key in shifts:
                                room_moves.append(shifts[key])
                model.Add(sum(room_moves) <= 1)

    # C4: No Batch can attend two classes at once
    for b in batches:
        for d_idx, day in enumerate(days):
            for slot in range(slots_per_day):
                batch_moves = []
                for t in teachers:
                    for s in subjects:
                        for r in rooms:
                            key = (t.id, s.id, b.id, r.id, day, slot)
                            if key in shifts:
                                batch_moves.append(shifts[key])
                model.Add(sum(batch_moves) <= 1)

    # --- 4. SOLVE ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Create a new Timetable Record
        dept = Department.objects.get(id=department_id)
        new_tt = GeneratedTimetable.objects.create(department=dept, status="DRAFT")

        count = 0
        # Extract results and save to DB
        for key, var in shifts.items():
            if solver.Value(var) == 1:
                t_id, s_id, b_id, r_id, day, slot_num = key

                # Convert slot_num to actual time (Simplified logic)
                start_hour = 9 + slot_num
                start_time = f"{start_hour:02d}:00"
                end_time = f"{start_hour + 1:02d}:00"

                TimetableSlot.objects.create(
                    timetable=new_tt,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    room_id=r_id,
                    teacher_id=t_id,
                    subject_id=s_id,
                    batch_id=b_id
                )
                count += 1

        return f"Optimization Successful! Created {count} slots in Timetable #{new_tt.id}"

    return "No solution found. Try adding more rooms or reducing lectures."