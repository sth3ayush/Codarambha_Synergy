from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=100)

    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class OTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        import random, string
        return ''.join(random.choices(string.digits, k=6))
    
class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

class HostProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="host_profile")
    government_id_photo = models.ImageField(upload_to="gov_ids")
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"Host: {self.user.email}"

class DriverProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver_profile")
    driving_license_photo = models.ImageField(upload_to="license")
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"Driver: {self.user.email}"

class ParkingSpot(models.Model):
    host = models.ForeignKey(
        "HostProfile", on_delete=models.CASCADE, related_name="parking_spots"
    )

    LAND_TYPES = [
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("institutional", "Institutional"),
        ("industrial", "Industrial"),
        ("public", "Public"),
        ("special", "Special")
    ]

    land_type = models.CharField(max_length=30, choices=LAND_TYPES)

    reference_landmark = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    street_address = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    city_town_village = models.CharField(max_length=100)

    security_features = models.JSONField(default=dict, blank=True)

    is_verified = models.BooleanField(default=False)
    is_secured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference_landmark} - {self.city_town_village}"
    
class ParkingSpotImages(models.Model):
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name="parking_images")
    parking_spot_image = models.ImageField(upload_to='parking_spot')

    def __str__(self):
        return f"{self.parking_spot.latitude} {self.parking_spot.longitude}"

class ParkingSpotCapacity(models.Model):
    parking_spot = models.ForeignKey(
        ParkingSpot, on_delete=models.CASCADE, related_name="capacities"
    )
 
    VEHICLE_CHOICES = [
        ("bicycle", "Bicycle"),
        ("car", "Car"),
        ("bike", "Bike"),
        ("truck", "Truck"),
    ]
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_CHOICES)

    total_spots = models.PositiveIntegerField(default=1)
    available_spots = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.total_spots} {self.vehicle_type}(s) at {self.parking_spot.reference_landmark}"
    
class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    actual_end_time = models.DateTimeField(blank=True, null=True) 
    ended = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.parking_spot.name}"