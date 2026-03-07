from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('profile/', views.voter_profile_view, name='voter_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/verify/', views.verify_reset_otp_view, name='verify_reset_otp'),
    path('forgot-password/reset/', views.reset_password_view, name='reset_password'),
]
