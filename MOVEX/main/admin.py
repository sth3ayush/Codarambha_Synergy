from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Fields to display in the admin list
    list_display = (
        'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'date_joined'
    )
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')

    # Fields for viewing/editing a user
    fieldsets = (
        (None, {
            'fields': ('email', 'password', 'first_name', 'last_name', 'phone_number')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'password1', 'password2', 'is_staff', 'is_active'
            )
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(HostProfile)
admin.site.register(DriverProfile)
admin.site.register(ParkingSpot)
admin.site.register(ParkingSpotCapacity)
admin.site.register(Booking)
admin.site.register(OTP)
admin.site.register(PhoneOTP)