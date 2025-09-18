from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from django.core.exceptions import ValidationError

def validate_pdf_file(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only PDF files are allowed.')

def validate_csv_file(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.csv']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only CSV files are allowed.')

def validate_audio_file(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only afrom udio files are allowed (mp3, wav, ogg, m4a, aac).')



class Student(AbstractUser):
    GRADE_CHOICES = [
        ('G1', 'Grade 1'),
        ('G2', 'Grade 2'),
        ('G3', 'Grade 3'),
        ('G4', 'Grade 4'),
        ('G5', 'Grade 5'),
        ('G6', 'Grade 6'),
        ('other', 'Other'),
    ]
    

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

import os
from django.db import models
from PyPDF2 import PdfReader, PdfWriter

from django.utils.text import slugify

def book_pdf_upload_path(instance, filename):
    slug = slugify(instance.title)
    return f"books/{instance.id or 'temp'}_{slug}/pdf/{filename}"

def book_answers_upload_path(instance, filename):
    slug = slugify(instance.title)
    return f"books/{instance.id or 'temp'}_{slug}/answers/{filename}"

def book_audio_upload_path(instance, filename):
    slug = slugify(instance.book.title)
    return f"books/{instance.book.id or 'temp'}_{slug}/audio/{filename}"


class Book(models.Model):
    GRADE_CHOICES = [
        ('G1', 'Grade 1'),
        ('G2', 'Grade 2'),
        ('G3', 'Grade 3'),
        ('G4', 'Grade 4'),
        ('G5', 'Grade 5'),
        ('G6', 'Grade 6'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES)
    description = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to=book_pdf_upload_path, validators=[validate_pdf_file])
    page_count = models.PositiveIntegerField()
    answers_file = models.FileField(upload_to=book_answers_upload_path, validators=[validate_csv_file], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to get ID
        if self.pdf_file:
            self.split_pdf_by_pages()

    def split_pdf_by_pages(self):
        pdf_path = self.pdf_file.path
        pdf_dir = os.path.join(os.path.dirname(pdf_path))
        reader = PdfReader(pdf_path)
        
        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            page_filename = os.path.join(pdf_dir, f'page_{i}.pdf')
            with open(page_filename, 'wb') as f:
                writer.write(f)

    def __str__(self):
        return self.title

class BookAudio(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='audios')
    page_number = models.PositiveIntegerField()
    audio_file = models.FileField(upload_to=book_audio_upload_path, validators=[validate_audio_file])
    audio_order = models.PositiveIntegerField(default=1)  # For multiple audios per page
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['page_number', 'audio_order']
        unique_together = ['book', 'page_number', 'audio_order']
    
    def __str__(self):
        return f"{self.book.title} - Page {self.page_number} - Audio {self.audio_order}"