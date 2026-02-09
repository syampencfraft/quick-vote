from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('profile/', views.voter_profile_view, name='voter_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
