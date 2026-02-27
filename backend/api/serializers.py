from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot, PinnedSlot

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class StudentBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBatch
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'name', 'email', 'department', 'preferred_start_slot', 'preferred_end_slot', 'max_classes_per_day', 'username', 'password']
        read_only_fields = ['user']

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        if not username or not password:
            raise serializers.ValidationError({"username": "Required for new faculty", "password": "Required"})

        try:
            user = User.objects.create_user(username=username, password=password)
        except Exception as e:
            raise serializers.ValidationError({"username": "This username is already taken."})

        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class PinnedSlotSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = PinnedSlot
        fields = '__all__'

class GeneratedTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedTimetable
        fields = '__all__'

class TimetableSlotSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)

    class Meta:
        model = TimetableSlot
        fields = '__all__'