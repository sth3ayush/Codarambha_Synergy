from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import *
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from twilio.rest import Client
from django.conf import settings
import random

User = get_user_model()

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('home')
        else: 
            messages.error(request, 'Email or Password is incorrect! Please try again.')
    
    context = {}
    return render(request, 'main/login.html', context)

def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            return JsonResponse({"status": "error", "message": "Email required"})

        otp_code = OTP.generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp_code}. Valid for 5 minutes.",
            "noreply@yourapp.com",
            [email],
            fail_silently=True,
        )

        return JsonResponse({"status": "success", "message": "OTP sent!"})
    
def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        otp_code = request.POST.get("otp")

        # Validate passwords
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # Verify OTP
        try:
            otp_obj = OTP.objects.filter(email=email, code=otp_code, is_verified=False).latest("created_at")
        except OTP.DoesNotExist:
            messages.error(request, "Invalid OTP")
            return redirect("register")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired")
            return redirect("register")

        otp_obj.is_verified = True
        otp_obj.save()

        # Create User
        if User.objects.filter(email=email).exists():
            messages.error(request, "User already exists")
            return redirect("register")

        user = User.objects.create_user(
            email=email,
            password=password1,
        )

        otp_obj.delete()

        login(request, user)
        messages.success(request, "Registration successful!")
        return redirect("home")

    return render(request, "main/register.html")

@login_required(login_url='login')
def logoutPage(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect('home')

def check_user_exists(request):
    if request.method == "POST":
        email = request.POST.get("email")
        exists = User.objects.filter(email=email).exists()
        return JsonResponse({"exists": exists})

def home(request):
    return render(request, "main/home.html")

def phoneOTP(request):
    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
    otp = str(random.randint(100000, 999999))

    if request.method == "POST":
        phone = request.POST.get("phone")
        if not phone:
            return JsonResponse({"status": "error", "message": "Phone Number required"})
        print(otp)
        PhoneOTP.objects.create(phone=phone, code=otp)
        client.messages.create(
            body=f'Your OTP is {otp}, please do not share it with anyone. Valid for 5 minutes.',
            from_='+12762901123',  # Twilio phone number
            to='+977' + phone
        )

        return JsonResponse({"status": "success", "message": "OTP sent!"})

@login_required(login_url='login')
def profileCreate(request):
    user = request.user

    if has_profile(user):
        # Already has base profile → if there’s a "next" stored, redirect there
        next_url = request.session.pop('next_after_profile', None)
        if next_url:
            return redirect(next_url)
        return redirect("home")

    if request.method == "POST":
        f_name = request.POST.get("f_name")
        l_name = request.POST.get("l_name")
        phone = request.POST.get("phone")
        otp_code = request.POST.get("otp")

        if not phone:
            messages.error(request, "Phone Number required")
            return redirect("profile-create")

        try:
            otp_obj = PhoneOTP.objects.filter(
                phone=phone, code=otp_code, is_verified=False
            ).latest("created_at")
        except PhoneOTP.DoesNotExist:
            messages.error(request, "Invalid OTP")
            return redirect("register")
        
        if otp_obj.is_expired():
            messages.error(request, "OTP expired")
            return redirect("register")
        
        otp_obj.is_verified = True
        otp_obj.save()

        if User.objects.filter(phone_number=phone).exclude(id=request.user.id).exists():
            messages.error(request, "Phone Number has already been used.")
            return redirect("profile-create")
        
        # Save user base profile
        user.first_name = f_name
        user.last_name = l_name
        user.phone_number = phone
        user.save()

        otp_obj.delete()

        messages.success(request, "Profile created successfully!")

        # If user was trying to become host/driver, redirect there
        next_url = request.session.pop('next_after_profile', None)
        if next_url:
            return redirect(next_url)

        return redirect("home")

    return render(request, "main/profile_create.html")


def check_phone_exists(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        exists = User.objects.filter(phone_number=phone).exists()
        return JsonResponse({"exists": exists})
    
def has_profile(user):
    return user.phone_number and (user.first_name or user.last_name)

@login_required(login_url='login')
def host_profile_create(request):
    user = request.user

    if HostProfile.objects.filter(user=user).exists():
        messages.warning(request, "You already have a Host Account.")
        return redirect('home')

    if not has_profile(user):
        # Store next step → Host
        request.session['next_after_profile'] = 'host-profile-create'
        return redirect('profile-create')

    if request.method == "POST":
        id_photo = request.FILES.get("gov_id_image")
        if not id_photo:
            messages.error(request, "No ID image uploaded.")
            return redirect('host-profile-create')

        try:
            HostProfile.objects.create(user=user, government_id_photo=id_photo)
            messages.success(request, "Host profile created successfully!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('host-profile-create')

    return render(request, "main/host_profile_form.html")

@login_required(login_url='login')
def driver_profile_create(request):
    user = request.user

    if DriverProfile.objects.filter(user=user).exists():
        messages.warning(request, "You already have a Driver Account.")
        return redirect('home')

    if not has_profile(user):
        request.session['next_after_profile'] = 'driver-profile-create'
        return redirect('profile-create')

    if request.method == "POST":
        license_photo = request.FILES.get("license_image")
        if not license_photo:
            messages.error(request, "No license image uploaded.")
            return redirect('driver-profile-create')

        try:
            DriverProfile.objects.create(user=user, driving_license_photo=license_photo)
            messages.success(request, "Driver profile created successfully!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('driver-profile-create')

    return render(request, "main/driver_profile_form.html")

@login_required(login_url='login')
def hostingPage(request):
    user = request.user

    if not HostProfile.objects.filter(user=user).exists():
        return redirect("host-profile-create")

    parking_spot_count = ParkingSpot.objects.filter(host__user=user).count()
    parking_spot = ParkingSpot.objects.filter(host__user=user)

    context = {"hide_nav_icons": True, "parking_spot_count":parking_spot_count, "parking_spot": parking_spot}
    return render(request, "main/hosting.html", context)