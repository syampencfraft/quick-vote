from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, OTP

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (StudentProfileInline,)
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'mobile_number', 'is_verified')}),
    )

class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'is_valid')
    readonly_fields = ('created_at',)

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True

admin.site.register(User, CustomUserAdmin)
admin.site.register(OTP, OTPAdmin)
# StudentProfile is inline, but can also be registered separately if needed
admin.site.register(StudentProfile)
