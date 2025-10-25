from .models import *

def userDetails(request):
    if request.user.is_authenticated:
        user = request.user

        driver_profile_exist = DriverProfile.objects.filter(user=user).exists()
        host_profile_exist = HostProfile.objects.filter(user=user).exists()

        return {
            'driver_profile_exists': driver_profile_exist, 
            'host_profile_exists': host_profile_exist
        }
    
    return {
        'driver_profile_exists': False, 
        'host_profile_exists': False
    }
