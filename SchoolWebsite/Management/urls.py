from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'students', views.StudentViewSet)
router.register(r'books', views.BookViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('overview/', views.dashboard_overview, name='dashboard_overview'),
    path('admin/login/', views.AdminAuthToken.as_view(), name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/verify/', views.verify_admin, name='verify_admin'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard-api'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    path('book/<int:book_id>/', views.get_book, name='book_api'),
    path('book/<int:book_id>/answers/', views.get_book_answers, name='book_answers_api'),
    path('audio', views.get_audios),
    path('test', views.test)
]