from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Department, StudentBatch, Teacher, Subject, Room, PinnedSlot


class Command(BaseCommand):
    help = 'Seed database with dummy data for testing'

    def handle(self, *args, **options):
        self.stdout.write("🗑️  Clearing old data...")
        TimetableSlot = __import__('api.models', fromlist=['TimetableSlot']).TimetableSlot
        GeneratedTimetable = __import__('api.models', fromlist=['GeneratedTimetable']).GeneratedTimetable
        TimetableSlot.objects.all().delete()
        GeneratedTimetable.objects.all().delete()
        PinnedSlot.objects.all().delete()
        Subject.objects.all().delete()
        Teacher.objects.all().delete()
        StudentBatch.objects.all().delete()
        Room.objects.all().delete()
        Department.objects.all().delete()
        # Don't delete superuser, only delete teacher-linked users
        User.objects.filter(is_staff=False, is_superuser=False).delete()

        # ─── Department ───
        self.stdout.write("🏫 Creating Department...")
        dept = Department.objects.create(name="uGDX")

        # ─── Main Batches (60 students each, used for theory lectures) ───
        self.stdout.write("👨‍🎓 Creating Student Batches...")
        voyagers = StudentBatch.objects.create(name="SY Voyagers", size=60, department=dept, max_classes_per_day=6)
        hadoop   = StudentBatch.objects.create(name="SY Hadoop",   size=60, department=dept, max_classes_per_day=6)

        # ─── Lab Sub-Batches (30 each — batch split in half for lab lectures) ───
        voyagers_lab_a = StudentBatch.objects.create(name="SY Voyagers - Lab A", size=30, department=dept, parent_batch=voyagers)
        voyagers_lab_b = StudentBatch.objects.create(name="SY Voyagers - Lab B", size=30, department=dept, parent_batch=voyagers)
        hadoop_lab_a   = StudentBatch.objects.create(name="SY Hadoop - Lab A",   size=30, department=dept, parent_batch=hadoop)
        hadoop_lab_b   = StudentBatch.objects.create(name="SY Hadoop - Lab B",   size=30, department=dept, parent_batch=hadoop)

        # ─── Rooms ───
        self.stdout.write("🏠 Creating Rooms...")
        Room.objects.create(name="Room 101",  capacity=60, is_lab=False)
        Room.objects.create(name="Room 102",  capacity=60, is_lab=False)
        Room.objects.create(name="Room 103",  capacity=60, is_lab=False)
        Room.objects.create(name="Room 101A", capacity=30, is_lab=True)
        Room.objects.create(name="Room 101B", capacity=30, is_lab=True)

        # ─── Teachers & Subjects ───
        self.stdout.write("👩‍🏫 Creating Teachers & Subjects...")

        def create_teacher(name, email_prefix):
            """Create a User + Teacher profile and return the Teacher."""
            username = email_prefix.lower()
            user = User.objects.create_user(
                username=username,
                password="pass1234",
                email=f"{username}@university.edu",
            )
            return Teacher.objects.create(
                user=user,
                name=name,
                email=f"{username}@university.edu",
                department=dept,
                preferred_start_slot=0,
                preferred_end_slot=8,
                max_classes_per_day=4,
            )

        def add_theory_subject(teacher, subject_name, code, weekly_lectures):
            """Create a theory subject for BOTH main batches."""
            for batch in [voyagers, hadoop]:
                Subject.objects.create(
                    name=subject_name, code=code,
                    weekly_lectures=weekly_lectures,
                    department=dept, batch=batch, teacher=teacher,
                )

        def add_lab_subject(teacher, subject_name, code):
            """Create a lab subject (1/week) for each lab sub-batch of BOTH batches."""
            for sub in [voyagers_lab_a, voyagers_lab_b, hadoop_lab_a, hadoop_lab_b]:
                Subject.objects.create(
                    name=f"{subject_name} - Lab",
                    code=f"{code}L",
                    weekly_lectures=1,
                    department=dept, batch=sub, teacher=teacher,
                )

        # 1. Sohel Das – Advanced Machine Learning (3 theory/week)
        t = create_teacher("Sohel Das", "sohel.das")
        add_theory_subject(t, "Advanced Machine Learning", "AML501", 3)

        # 2. Shashikant Patil – Business Plan Writing (3 theory/week)
        t = create_teacher("Shashikant Patil", "shashikant.patil")
        add_theory_subject(t, "Business Plan Writing", "BPW502", 3)

        # 3. Yogesh Jadhav – Data Engineering Operations (3 theory + 1 lab/week)
        t = create_teacher("Yogesh Jadhav", "yogesh.jadhav")
        add_theory_subject(t, "Data Engineering Operations", "DEO503", 3)
        add_lab_subject(t, "Data Engineering Operations", "DEO503")

        # 4. Nimesh Bumb – Introduction to Algorithms (3 theory/week)
        t = create_teacher("Nimesh Bumb", "nimesh.bumb")
        add_theory_subject(t, "Introduction to Algorithms", "ITA504", 3)

        # 5. Sujatha Ayyengar – Large-Scale Data Storage (3 theory/week)
        t = create_teacher("Sujatha Ayyengar", "sujatha.ayyengar")
        add_theory_subject(t, "Large-Scale Data Storage", "LDS505", 3)

        # 6. Kunal Meher – DevOps and MLOps (3 theory + 1 lab/week)
        t = create_teacher("Kunal Meher", "kunal.meher")
        add_theory_subject(t, "DevOps and MLOps", "DOM506", 3)
        add_lab_subject(t, "DevOps and MLOps", "DOM506")

        # 7. Firoz Shaikh – Career Services (2 theory/week)
        t = create_teacher("Firoz Shaikh", "firoz.shaikh")
        add_theory_subject(t, "Career Services", "CS507", 2)

        # 8. Elective – Pinned to Wednesday 10:00–12:00 (2 consecutive slots)
        #    Each batch gets its own elective teacher to avoid teacher-conflict at same slot
        for i, batch in enumerate([voyagers, hadoop], start=1):
            elective_teacher = create_teacher(f"Elective Faculty {i}", f"elective.faculty{i}")
            elective_subj = Subject.objects.create(
                name="Elective",
                code="ELEC500",
                weekly_lectures=2,
                department=dept,
                batch=batch,
                teacher=elective_teacher,
            )
            # Pin to Wednesday slot 2 (10:00–11:00) and slot 3 (11:00–12:00)
            PinnedSlot.objects.create(subject=elective_subj, department=dept, day='WED', slot_index=2)
            PinnedSlot.objects.create(subject=elective_subj, department=dept, day='WED', slot_index=3)
        self.stdout.write("📌 Elective pinned to Wednesday 10:00–12:00 for all batches")

        # ─── Admin superuser ───
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                password="admin123",
                email="admin@university.edu",
            )
            self.stdout.write("🔑 Admin superuser created (admin / admin123)")

        # ─── Summary ───
        theory_count = Subject.objects.exclude(name__endswith="- Lab").count()
        lab_count    = Subject.objects.filter(name__endswith="- Lab").count()

        self.stdout.write(self.style.SUCCESS("\n✅ Dummy data created successfully!"))
        self.stdout.write(f"   Department  : {dept.name}")
        self.stdout.write(f"   Batches     : {voyagers.name}, {hadoop.name} (60 students each, max 6 classes/day)")
        self.stdout.write(f"   Lab groups  : 4 sub-batches of 30 (each batch split in half for labs)")
        self.stdout.write(f"   Teachers    : {Teacher.objects.count()} (max 4 classes/day each)")
        self.stdout.write(f"   Subjects    : {Subject.objects.count()} total ({theory_count} theory + {lab_count} lab)")
        self.stdout.write(f"   Rooms       : {Room.objects.count()} (3 classrooms + 2 labs @ 30 cap)")
        self.stdout.write("")
        self.stdout.write("   📚 Subjects with lab sessions (batch split into 2 × 30 for labs):")
        self.stdout.write("      - Data Engineering Operations (DEO503) → 3 theory + 1 lab/week per sub-batch")
        self.stdout.write("      - DevOps and MLOps (DOM506)            → 3 theory + 1 lab/week per sub-batch")
        self.stdout.write("")
        self.stdout.write("   📌 Pinned/Fixed slots:")
        self.stdout.write("      - Elective (ELEC500) → Wednesday 10:00–12:00 (2 consecutive slots, all batches)")
        self.stdout.write("")
        self.stdout.write("   🆕 New Features:")
        self.stdout.write("      - Multi-variant generation (3 timetable options)")
        self.stdout.write("      - Review/Approval workflow (DRAFT → PUBLISHED)")
        self.stdout.write("      - Fixed/Pinned slots support")
        self.stdout.write("      - Max classes per day (teacher & batch)")
        self.stdout.write("      - Conflict diagnostics")
        self.stdout.write("      - PDF export")
        self.stdout.write("")
        self.stdout.write("   🔑 Login credentials:")
        self.stdout.write("      Admin     : admin / admin123")
        self.stdout.write("      Teachers  : <firstname.lastname> / pass1234")
        self.stdout.write("        e.g. sohel.das / pass1234")



