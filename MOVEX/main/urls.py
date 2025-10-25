from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.loginPage, name="login"),
    path('register/', views.registerPage, name='register'),
    path('logout/', views.logoutPage, name="logout"),

    path("check-user-exists/", views.check_user_exists, name="check-user-exists"),
    path("check-phone-exists/", views.check_phone_exists, name="check-phone-exists"),
    
    path("send-otp/", views.send_otp, name="send-otp"),
    path("verify-otp/", views.phoneOTP, name="phone-otp"),

    path("create-profile/", views.profileCreate, name="profile-create"),
    path("host-profile-create/", views.host_profile_create, name="host-profile-create"),
    path("driver-profile-create/", views.driver_profile_create, name="driver-profile-create"),

    path("hosting/", views.hostingPage, name="hosting"),
]