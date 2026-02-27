from ortools.sat.python import cp_model
from .models import Room, Teacher, Subject, StudentBatch, TimetableSlot, GeneratedTimetable, Department, PinnedSlot


DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']
TIME_SLOTS = ["07:30", "08:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
SLOTS_PER_DAY = len(TIME_SLOTS)


def run_diagnostics(department_id, batches, subjects, teachers, rooms):
    """Pre-solve diagnostics: detect obvious infeasibility before running the solver."""
    issues = []

    main_batches = [b for b in batches if b.parent_batch is None]
    sub_batches = [b for b in batches if b.parent_batch is not None]
    lab_rooms = [r for r in rooms if r.is_lab]
    theory_rooms = [r for r in rooms if not r.is_lab]

    total_theory_slots_needed = {}
    for b in main_batches:
        batch_subjects = [s for s in subjects if s.batch_id == b.id]
        total = sum(s.weekly_lectures for s in batch_subjects)
        total_theory_slots_needed[b.id] = total
        available = SLOTS_PER_DAY * len(DAYS)
        if total > available:
            issues.append(f"⚠️ Batch '{b.name}' needs {total} theory slots/week but only {available} slots exist (8 slots × 5 days).")

    if len(main_batches) > len(theory_rooms):
        issues.append(f"⚠️ {len(main_batches)} batches need simultaneous theory classes but only {len(theory_rooms)} theory rooms available. Add more rooms or stagger schedules.")

    for t in teachers:
        avail_slots = (t.preferred_end_slot - t.preferred_start_slot) * len(DAYS)
        teacher_subjects = [s for s in subjects if s.teacher_id == t.id]
        total_lectures = sum(s.weekly_lectures for s in teacher_subjects)
        if total_lectures > avail_slots:
            issues.append(f"⚠️ Teacher '{t.name}' has {total_lectures} lectures/week but only {avail_slots} available slots (preference: slot {t.preferred_start_slot}–{t.preferred_end_slot}).")
        max_daily = t.max_classes_per_day * len(DAYS)
        if total_lectures > max_daily:
            issues.append(f"⚠️ Teacher '{t.name}' has {total_lectures} lectures/week but max {t.max_classes_per_day}/day × 5 days = {max_daily}.")

    lab_subjects_by_parent = {}
    for s in subjects:
        if s.batch and s.batch.parent_batch:
            lab_subjects_by_parent.setdefault(s.batch.parent_batch_id, []).append(s)

    for parent_id, lab_subs in lab_subjects_by_parent.items():
        parent = next((b for b in main_batches if b.id == parent_id), None)
        sub_ids = set(s.batch_id for s in lab_subs)
        if len(sub_ids) >= 2 and len(lab_rooms) < len(sub_ids):
            issues.append(f"⚠️ Batch '{parent.name if parent else parent_id}' has {len(sub_ids)} lab sub-batches but only {len(lab_rooms)} lab rooms.")

    return issues


def _build_and_solve(department_id, batches, subjects, teachers, rooms, pinned_slots, variant_seed, variant_weight):
    """Build and solve a single CP-SAT model. Returns (status_str, slot_data_list, diagnostics_list)."""
    model = cp_model.CpModel()

    main_batches = [b for b in batches if b.parent_batch is None]
    lab_subjects = [s for s in subjects if s.batch and s.batch.parent_batch]
    theory_subjects = [s for s in subjects if s.batch and not s.batch.parent_batch]

    lab_groups_by_parent = {}
    for s in lab_subjects:
        parent_id = s.batch.parent_batch_id
        lab_groups_by_parent.setdefault(parent_id, {}).setdefault(s.batch.id, []).append(s)

    # Build pinned lookup: (subject_id, day, slot) -> True
    pinned_lookup = set()
    for p in pinned_slots:
        pinned_lookup.add((p.subject_id, p.day, p.slot_index))

    # 2. Create Variables
    shifts = {}
    for s in subjects:
        target_batch = s.batch
        if not target_batch:
            continue
        t = s.teacher
        if not t:
            continue
        is_lab_subject = target_batch.parent_batch is not None
        for r in rooms:
            if target_batch.size > r.capacity:
                continue
            if is_lab_subject and not r.is_lab:
                continue
            if not is_lab_subject and r.is_lab:
                continue
            for d_idx, day in enumerate(DAYS):
                for slot in range(SLOTS_PER_DAY):
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot:
                        continue
                    key = (t.id, s.id, target_batch.id, r.id, day, slot)
                    shifts[key] = model.NewBoolVar(f'shift_{key}')

    # 3. Hard Constraints

    # C1: Weekly Lectures
    for s in subjects:
        if not s.batch or not s.teacher:
            continue
        candidates = []
        for r in rooms:
            if s.batch.size > r.capacity:
                continue
            for day in DAYS:
                for slot in range(SLOTS_PER_DAY):
                    t = s.teacher
                    if slot < t.preferred_start_slot or slot >= t.preferred_end_slot:
                        continue
                    key = (t.id, s.id, s.batch.id, r.id, day, slot)
                    if key in shifts:
                        candidates.append(shifts[key])
        if candidates:
            model.Add(sum(candidates) == s.weekly_lectures)

    # C2: Teacher Conflict
    for t in teachers:
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                moves = [var for k, var in shifts.items()
                         if k[0] == t.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # C3: Room Conflict
    for r in rooms:
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                moves = [var for k, var in shifts.items() if k[3] == r.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # C4: Batch/Student Conflict
    for b in main_batches:
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                moves = [var for k, var in shifts.items()
                         if k[2] == b.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    sub_batches = [b for b in batches if b.parent_batch is not None]
    for b in sub_batches:
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                moves = [var for k, var in shifts.items()
                         if k[2] == b.id and k[4] == day and k[5] == slot]
                if moves:
                    model.Add(sum(moves) <= 1)

    # Parent-child exclusion
    for mb in main_batches:
        sub_ids = [sb.id for sb in batches if sb.parent_batch_id == mb.id]
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                theory_vars = [var for k, var in shifts.items()
                               if k[2] == mb.id and k[4] == day and k[5] == slot]
                lab_vars = [var for k, var in shifts.items()
                            if k[2] in sub_ids and k[4] == day and k[5] == slot]
                if theory_vars and lab_vars:
                    has_theory = model.NewBoolVar(f'theory_{mb.id}_{day}_{slot}')
                    model.Add(sum(theory_vars) >= 1).OnlyEnforceIf(has_theory)
                    model.Add(sum(theory_vars) == 0).OnlyEnforceIf(has_theory.Not())
                    model.Add(sum(lab_vars) == 0).OnlyEnforceIf(has_theory)

    # C5: At most one lecture per subject per day (relaxed for pinned subjects)
    # Count how many pins each subject has per day
    pins_per_subject_day = {}
    for p in pinned_slots:
        key = (p.subject_id, p.day)
        pins_per_subject_day[key] = pins_per_subject_day.get(key, 0) + 1

    for s in subjects:
        if not s.batch or not s.teacher:
            continue
        for day in DAYS:
            day_vars = [var for k, var in shifts.items() if k[1] == s.id and k[2] == s.batch.id and k[4] == day]
            if day_vars:
                # Allow more than 1 if there are multiple pins on this day for this subject
                max_on_day = max(1, pins_per_subject_day.get((s.id, day), 0))
                model.Add(sum(day_vars) <= max_on_day)

    # C6: Lab synchronization
    for parent_id, sub_batch_labs in lab_groups_by_parent.items():
        sub_batch_ids = list(sub_batch_labs.keys())
        if len(sub_batch_ids) < 2:
            continue
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                sub_vars = {}
                for sb_id in sub_batch_ids:
                    sv = [var for k, var in shifts.items()
                          if k[2] == sb_id and k[4] == day and k[5] == slot]
                    if sv:
                        sub_vars[sb_id] = sv
                if len(sub_vars) < 2:
                    continue
                lab_here = model.NewBoolVar(f'lab_{parent_id}_{day}_{slot}')
                for sb_id, sv in sub_vars.items():
                    model.Add(sum(sv) == 1).OnlyEnforceIf(lab_here)
                    model.Add(sum(sv) == 0).OnlyEnforceIf(lab_here.Not())

    # C7: Max classes per day — Teacher
    for t in teachers:
        for day in DAYS:
            day_vars = [var for k, var in shifts.items() if k[0] == t.id and k[4] == day]
            if day_vars:
                model.Add(sum(day_vars) <= t.max_classes_per_day)

    # C8: Max classes per day — Batch (main batches including their sub-batch labs)
    for mb in main_batches:
        batch_ids = [mb.id] + [sb.id for sb in batches if sb.parent_batch_id == mb.id]
        for day in DAYS:
            day_vars = [var for k, var in shifts.items() if k[2] in batch_ids and k[4] == day]
            if day_vars:
                model.Add(sum(day_vars) <= mb.max_classes_per_day)

    # C9: Pinned Slots — force specific subjects to specific day/slot
    for p in pinned_slots:
        s = next((sub for sub in subjects if sub.id == p.subject_id), None)
        if not s or not s.batch or not s.teacher:
            continue
        pin_vars = [var for k, var in shifts.items()
                    if k[1] == s.id and k[2] == s.batch.id and k[4] == p.day and k[5] == p.slot_index]
        if pin_vars:
            model.Add(sum(pin_vars) == 1)

    # 4. Optimization
    obj_terms = []

    # O1: Prefer earlier slots (with variant weight for diversity)
    for k, var in shifts.items():
        slot_idx = k[5]
        obj_terms.append(slot_idx * variant_weight * var)

    # O2: Minimize gaps
    for mb in main_batches:
        batch_ids = [mb.id] + [sb.id for sb in batches if sb.parent_batch_id == mb.id]
        for day in DAYS:
            day_vars_by_slot = {}
            for slot in range(SLOTS_PER_DAY):
                slot_vars = [var for k, var in shifts.items() if k[2] in batch_ids and k[4] == day and k[5] == slot]
                if slot_vars:
                    has_class = model.NewBoolVar(f'has_{mb.id}_{day}_{slot}')
                    model.Add(sum(slot_vars) >= 1).OnlyEnforceIf(has_class)
                    model.Add(sum(slot_vars) == 0).OnlyEnforceIf(has_class.Not())
                    day_vars_by_slot[slot] = has_class
            for slot, has_var in day_vars_by_slot.items():
                obj_terms.append(slot * 2 * has_var)

    model.Minimize(sum(obj_terms))

    # 5. Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.random_seed = variant_seed

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        slot_data = []
        for key, var in shifts.items():
            if solver.Value(var) == 1:
                t_id, s_id, b_id, r_id, day, slot_num = key
                start_str = TIME_SLOTS[slot_num]
                if slot_num == 1:
                    end_str = "09:30"
                else:
                    h, m = map(int, start_str.split(':'))
                    end_str = f"{h + 1:02d}:{m:02d}"
                slot_data.append({
                    'day': day, 'start_time': start_str, 'end_time': end_str,
                    'room_id': r_id, 'teacher_id': t_id, 'subject_id': s_id, 'batch_id': b_id,
                })
        return 'success', slot_data, []
    else:
        return 'infeasible', [], []


def generate_timetable(department_id, num_variants=3):
    """Generate multiple timetable variants. Returns a dict with status, messages, and timetable_ids."""

    batches = list(StudentBatch.objects.filter(department_id=department_id))
    subjects = list(Subject.objects.filter(department_id=department_id))
    teachers = list(Teacher.objects.filter(department_id=department_id))
    rooms = list(Room.objects.all())
    pinned_slots = list(PinnedSlot.objects.filter(department_id=department_id))

    if not teachers or not subjects or not batches:
        return {
            'status': 'error',
            'messages': ["Missing data. Need at least one Teacher, Subject, and Batch."],
            'timetable_ids': []
        }

    # Pre-solve diagnostics
    diagnostics = run_diagnostics(department_id, batches, subjects, teachers, rooms)

    dept = Department.objects.get(id=department_id)
    # Delete old DRAFTs (keep PUBLISHED)
    GeneratedTimetable.objects.filter(department=dept, status='DRAFT').delete()

    variant_configs = [
        {'seed': 42, 'weight': 1},
        {'seed': 137, 'weight': 2},
        {'seed': 7919, 'weight': 3},
    ]

    created_ids = []
    all_failed = True

    for i in range(min(num_variants, len(variant_configs))):
        cfg = variant_configs[i]
        status, slot_data, _ = _build_and_solve(
            department_id, batches, subjects, teachers, rooms, pinned_slots,
            variant_seed=cfg['seed'], variant_weight=cfg['weight']
        )

        if status == 'success':
            all_failed = False
            tt = GeneratedTimetable.objects.create(
                department=dept, status='DRAFT', variant_number=i + 1
            )
            for sd in slot_data:
                TimetableSlot.objects.create(timetable=tt, **sd)
            created_ids.append(tt.id)

    if all_failed:
        diagnostics.append("❌ Solver could not find a feasible schedule for any variant. Review the diagnostics above and adjust constraints.")
        return {
            'status': 'infeasible',
            'messages': diagnostics,
            'timetable_ids': []
        }

    return {
        'status': 'success',
        'messages': diagnostics if diagnostics else [f"✅ Generated {len(created_ids)} timetable variant(s) successfully!"],
        'timetable_ids': created_ids
    }
