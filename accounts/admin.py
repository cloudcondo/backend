from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import UnitAccess, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "condo", "created_at", "updated_at")
    list_filter = ("role", "condo")
    search_fields = ("user__username", "user__email", "phone")


class UnitAccessInline(admin.TabularInline):
    model = UnitAccess
    extra = 0
    autocomplete_fields = ("unit",)
    fields = ("unit", "access_type", "active", "created_at")
    readonly_fields = ("created_at",)


class UserAdmin(DjangoUserAdmin):
    inlines = [UnitAccessInline]


# Re-register User with inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UnitAccess)
class UnitAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "unit", "access_type", "active", "created_at", "updated_at")
    list_filter = ("access_type", "active", "unit__condo")
    search_fields = ("user__username", "user__email", "unit__unit_number")
    autocomplete_fields = ("user", "unit")
