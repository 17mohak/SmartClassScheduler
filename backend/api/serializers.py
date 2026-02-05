from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot

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
    # Add these fields to the API input, but write_only (don't send them back in responses)
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'name', 'email', 'department', 'preferred_start_slot', 'preferred_end_slot', 'username', 'password']
        read_only_fields = ['user'] # Don't let anyone manually set the user ID

    def create(self, validated_data):
        # 1. Extract the login credentials
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        if not username or not password:
            raise serializers.ValidationError({"username": "Required for new faculty", "password": "Required"})

        # 2. Create the Auth User
        try:
            user = User.objects.create_user(username=username, password=password)
        except Exception as e:
            raise serializers.ValidationError({"username": "This username is already taken."})

        # 3. Create the Teacher Profile linked to that User
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class GeneratedTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedTimetable
        fields = '__all__'

class TimetableSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableSlot
        fields = '__all__'