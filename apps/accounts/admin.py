from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile / role"


class UserAdminWithProfile(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ("username", "email", "get_role", "is_staff")

    @admin.display(description="Role")
    def get_role(self, obj):
        return getattr(getattr(obj, "profile", None), "role", "—")


admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfile)
