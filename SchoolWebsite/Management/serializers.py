from rest_framework import serializers
from .models import Student, Book, BookAudio

class StudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'grade', 'password', 'created_at']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        student = Student.objects.create_user(**validated_data)
        student.set_password(password)
        student.save()
        return student
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class BookAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookAudio
        fields = ['id', 'page_number', 'audio_file', 'audio_order']

class BookSerializer(serializers.ModelSerializer):
    audios = BookAudioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'grade', 'description', 'pdf_file', 'page_count', 'answers_file', 'audios', 'created_at', 'updated_at']
