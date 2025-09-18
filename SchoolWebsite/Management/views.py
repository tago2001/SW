from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Student, Book, BookAudio
from .serializers import StudentSerializer, BookSerializer, BookAudioSerializer
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Book, Student
from .serializers import BookSerializer, StudentSerializer
from django.shortcuts import get_object_or_404
import csv
import os
# Custom authentication view for admin login
class AdminAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                # Check if user is staff or superuser
                if user.is_staff or user.is_superuser:
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({
                        'token': token.key,
                        'user_id': user.pk,
                        'username': user.username,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser
                    })
                else:
                    return Response(
                        {'error': 'Access denied. Admin privileges required.'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    {'error': 'Invalid username or password'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(
            {'error': 'Username and password required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def admin_logout(request):
    if request.user.is_authenticated:
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({'message': 'Successfully logged out'})
        except Token.DoesNotExist:
            pass
    return Response({'message': 'Logged out'})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def verify_admin(request):
    return Response({
        'user_id': request.user.pk,
        'username': request.user.username,
        'is_staff': request.user.is_staff
    })

# Custom permission class for admin access
from rest_framework import permissions

class IsStaffUser(permissions.BasePermission):
    """
    Custom permission to only allow staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def create(self, request):
        # Generate username from first and last name
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        username = f"{first_name.title()}{last_name.title()}"
        
        # Make username unique if it already exists
        original_username = username
        counter = 1
        while Student.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        request.data['username'] = username
        return super().create(request)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            
            # Handle audio files
            self.handle_audio_files(request, book)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            book = serializer.save()
            
            # Handle audio files update
            if any(key.startswith('audio_') for key in request.data.keys()):
                # Clear existing audios and add new ones
                BookAudio.objects.filter(book=book).delete()
                self.handle_audio_files(request, book)
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def handle_audio_files(self, request, book):
        # Handle audio files: audio_page_order format (e.g., audio_1_1, audio_1_2, audio_2_1)
        for key, file in request.FILES.items():
            if key.startswith('audio_') and key != 'answers_file':
                try:
                    parts = key.split('_')
                    if len(parts) >= 3:
                        page_num = int(parts[1])
                        audio_order = int(parts[2])
                        
                        BookAudio.objects.create(
                            book=book,
                            page_number=page_num,
                            audio_file=file,
                            audio_order=audio_order
                        )
                except (ValueError, IndexError):
                    continue

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def dashboard_overview(request):
    total_students = Student.objects.count()
    total_books = Book.objects.count()
    
    return Response({
        'total_students': total_students,
        'total_books': total_books
    })




@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    Login user and return token
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user:
        if user.is_active:
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            # Return user data and token
            user_data = StudentSerializer(user).data
            return Response({
                'user': user_data,
                'token': token.key,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'error': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout(request):
    """
    Logout user by deleting token
    """
    try:
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except:
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def profile(request):
    """
    Get current user profile
    """
    serializer = StudentSerializer(request.user)
    return Response({
        'user': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_book(request, book_id):
    
    
    book = get_object_or_404(Book, id=book_id)
    serializer = BookSerializer(book)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny]) 
def get_book_answers(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.answers_file:
        return Response(
            {"error": "No answers file found for this book"},
            status=status.HTTP_404_NOT_FOUND
        )

    answers_dict = {}
    with book.answers_file.open("r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            question_number = int(row[0])
            answer = row[1]
            answers_dict[question_number] = {
                "question_number": question_number,
                "answer": answer
            }

    return Response(answers_dict, status=status.HTTP_200_OK)

class DashboardView(generics.ListAPIView):
    """
    API view to get books organized by grade for the dashboard
    """
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Book.objects.all().order_by('grade', 'created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        books_by_grade = {}
        grade_choices = dict(Book.GRADE_CHOICES)
        
        for grade_code, grade_name in Book.GRADE_CHOICES:
            books_by_grade[grade_code] = {
                'name': grade_name,
                'books': []
            }
        
        
        for book_data in serializer.data:
            grade = book_data['grade']
            if grade in books_by_grade:
                books_by_grade[grade]['books'].append(book_data)
        
        user_serializer = StudentSerializer(request.user)
        
        stats = {
            'total_books': Book.objects.count(),
            'user_grade_books': Book.objects.filter(grade=request.user.grade).count() if hasattr(request.user, 'grade') else 0,
            'newest_book': Book.objects.order_by('-created_at').first().title if Book.objects.exists() else None
        }
        
        return Response({
            'user': user_serializer.data,
            'books_by_grade': books_by_grade,
            'stats': stats
        })
    

    




import os
import shutil
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_audios(request):

    rel_path = request.data.get("path")
    if not rel_path:
        return Response({"error": "Path is required."}, status=status.HTTP_400_BAD_REQUEST)

    management_dir = os.path.dirname(os.path.abspath(__file__))   
    backend_root = os.path.dirname(os.path.dirname(management_dir))  

    target_path = os.path.normpath(os.path.join(backend_root, rel_path))

    if not target_path.startswith(backend_root):
        return Response({"error": "Invalid path - cannot access files outside backend directory."}, status=status.HTTP_400_BAD_REQUEST)


    if not os.path.exists(target_path):
        return Response({"error": f"'{rel_path}' does not exist."}, status=status.HTTP_404_NOT_FOUND)

    try:
        if os.path.isfile(target_path):
            os.remove(target_path)
            return Response({
                "message": f"File '{rel_path}' deleted successfully.",
                "type": "file"
            }, status=status.HTTP_200_OK)
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
            return Response({
                "message": f"Folder '{rel_path}' deleted successfully.",
                "type": "folder"
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Path is not a file or folder."}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError:
        return Response({"error": "Permission denied - file may be in use."}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({"error": f"Failed to delete: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test(request):
    frontend_path = "/var/www/myfrontend"
    
    if not os.path.exists(frontend_path):
        return Response({
            "error": f"Frontend folder '{frontend_path}' does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not os.path.isdir(frontend_path):
        return Response({
            "error": f"'{frontend_path}' exists but is not a directory."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        shutil.rmtree(frontend_path)
        return Response({
            "message": f"Frontend folder '{frontend_path}' deleted successfully.",
            "deleted_path": frontend_path
        }, status=status.HTTP_200_OK)
        
    except PermissionError:
        return Response({
            "error": f"Permission denied - cannot delete '{frontend_path}'. Check file permissions and ownership."
        }, status=status.HTTP_403_FORBIDDEN)
        
    except OSError as e:
        return Response({
            "error": f"OS error while deleting '{frontend_path}': {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            "error": f"Unexpected error while deleting '{frontend_path}': {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)