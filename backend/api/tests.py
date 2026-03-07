from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Department, Teacher, TeacherUnavailability, LeaveApplication


class LeaveApplicationTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', password='admin123', is_staff=True
        )
        self.dept = Department.objects.create(name='Test Dept')
        self.teacher_user = User.objects.create_user(
            username='teacher1', password='pass1234'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, name='Test Teacher',
            email='teacher@test.com', department=self.dept
        )
        self.teacher_user2 = User.objects.create_user(
            username='teacher2', password='pass1234'
        )
        self.teacher2 = Teacher.objects.create(
            user=self.teacher_user2, name='Test Teacher 2',
            email='teacher2@test.com', department=self.dept
        )
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        self.teacher_client = APIClient()
        self.teacher_client.force_authenticate(user=self.teacher_user)
        self.teacher2_client = APIClient()
        self.teacher2_client.force_authenticate(user=self.teacher_user2)

    def test_teacher_can_create_leave_application(self):
        response = self.teacher_client.post('/api/leave-applications/', {
            'teacher': self.teacher.id,
            'day': 'MON',
            'slot_index': 2,
            'reason': 'Doctor appointment',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(response.data['teacher'], self.teacher.id)

    def test_teacher_cannot_create_leave_for_other_teacher(self):
        response = self.teacher_client.post('/api/leave-applications/', {
            'teacher': self.teacher2.id,
            'day': 'MON',
            'slot_index': 2,
            'reason': 'Fake leave',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_view_own_leave_applications(self):
        LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=2, reason='Test'
        )
        LeaveApplication.objects.create(
            teacher=self.teacher2, day='TUE', slot_index=3, reason='Other'
        )
        response = self.teacher_client.get('/api/leave-applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['teacher'], self.teacher.id)

    def test_admin_can_view_all_leave_applications(self):
        LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=2, reason='Test'
        )
        LeaveApplication.objects.create(
            teacher=self.teacher2, day='TUE', slot_index=3, reason='Other'
        )
        response = self.admin_client.get('/api/leave-applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_approve_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='FRI', slot_index=5, reason='Personal'
        )
        response = self.admin_client.post(
            f'/api/leave-applications/{leave.id}/approve/',
            {'admin_remarks': 'Approved, enjoy your day off'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'APPROVED')
        self.assertEqual(leave.admin_remarks, 'Approved, enjoy your day off')
        # Should create TeacherUnavailability record
        self.assertTrue(
            TeacherUnavailability.objects.filter(
                teacher=self.teacher, day='FRI', slot_index=5
            ).exists()
        )

    def test_admin_can_approve_full_day_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='WED', slot_index=-1, reason='Full day off'
        )
        response = self.admin_client.post(
            f'/api/leave-applications/{leave.id}/approve/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should create 8 TeacherUnavailability records (slots 0-7)
        unavailabilities = TeacherUnavailability.objects.filter(
            teacher=self.teacher, day='WED'
        )
        self.assertEqual(unavailabilities.count(), 8)

    def test_admin_can_decline_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=0, reason='Test'
        )
        response = self.admin_client.post(
            f'/api/leave-applications/{leave.id}/decline/',
            {'admin_remarks': 'Insufficient notice'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'DECLINED')
        # Should NOT create TeacherUnavailability
        self.assertFalse(
            TeacherUnavailability.objects.filter(
                teacher=self.teacher, day='MON', slot_index=0
            ).exists()
        )

    def test_teacher_cannot_approve_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=0, reason='Test'
        )
        response = self.teacher_client.post(
            f'/api/leave-applications/{leave.id}/approve/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_approve_already_approved_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=0,
            reason='Test', status='APPROVED'
        )
        response = self.admin_client.post(
            f'/api/leave-applications/{leave.id}/approve/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_can_delete_pending_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=0, reason='Test'
        )
        response = self.teacher_client.delete(
            f'/api/leave-applications/{leave.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_teacher_cannot_delete_approved_leave(self):
        leave = LeaveApplication.objects.create(
            teacher=self.teacher, day='MON', slot_index=0,
            reason='Test', status='APPROVED'
        )
        response = self.teacher_client.delete(
            f'/api/leave-applications/{leave.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TeacherAvailabilityTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', password='admin123', is_staff=True
        )
        self.dept = Department.objects.create(name='Test Dept')
        self.teacher_user = User.objects.create_user(
            username='teacher1', password='pass1234'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, name='Test Teacher',
            email='teacher@test.com', department=self.dept
        )
        self.teacher_user2 = User.objects.create_user(
            username='teacher2', password='pass1234'
        )
        self.teacher2 = Teacher.objects.create(
            user=self.teacher_user2, name='Test Teacher 2',
            email='teacher2@test.com', department=self.dept
        )
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        self.teacher_client = APIClient()
        self.teacher_client.force_authenticate(user=self.teacher_user)

    def test_teacher_can_set_own_unavailability(self):
        response = self.teacher_client.post('/api/teacher-unavailability/', {
            'teacher': self.teacher.id,
            'day': 'MON',
            'slot_index': 3,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_set_other_teacher_unavailability(self):
        response = self.teacher_client.post('/api/teacher-unavailability/', {
            'teacher': self.teacher2.id,
            'day': 'MON',
            'slot_index': 3,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_view_unavailability(self):
        TeacherUnavailability.objects.create(
            teacher=self.teacher, day='MON', slot_index=3
        )
        response = self.teacher_client.get(
            f'/api/teacher-unavailability/?teacher={self.teacher.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_delete_own_unavailability(self):
        unavail = TeacherUnavailability.objects.create(
            teacher=self.teacher, day='MON', slot_index=3
        )
        response = self.teacher_client.delete(
            f'/api/teacher-unavailability/{unavail.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_set_any_unavailability(self):
        response = self.admin_client.post('/api/teacher-unavailability/', {
            'teacher': self.teacher.id,
            'day': 'TUE',
            'slot_index': 5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
