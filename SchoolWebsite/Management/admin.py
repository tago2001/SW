from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Student, Book, BookAudio

@admin.register(Student)
class StudentAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'grade', 'created_at')
    list_filter = ('grade', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',)
    
    fieldsets = list(UserAdmin.fieldsets) + [
    ('Student Info', {'fields': ('grade',)}),
    ]

    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Student Info', {'fields': ('first_name', 'last_name', 'email', 'grade')}),
    )

class BookAudioInline(admin.TabularInline):
    model = BookAudio
    extra = 0
    ordering = ['page_number', 'audio_order']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'page_count', 'created_at', 'updated_at')
    list_filter = ('grade', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    inlines = [BookAudioInline]

@admin.register(BookAudio)
class BookAudioAdmin(admin.ModelAdmin):
    list_display = ('book', 'page_number', 'audio_order', 'created_at')
    list_filter = ('book', 'page_number')
    ordering = ['book', 'page_number', 'audio_order']


