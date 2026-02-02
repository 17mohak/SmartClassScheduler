from rest_framework import serializers
from .models import Room, Teacher, Subject, StudentBatch, Department, GeneratedTimetable, TimetableSlot

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class StudentBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBatch
        fields = '__all__'

class GeneratedTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedTimetable
        fields = '__all__'

class TimetableSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableSlot
        fields = '__all__'